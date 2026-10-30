import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def normalized_customer_id(value) -> str | None:
    if pd.isna(value):
        return None
    text_value = str(value).strip()
    if not text_value or text_value.lower() == "nan":
        return None
    if text_value.endswith(".0"):
        text_value = text_value[:-2]
    return text_value


def load_source() -> tuple[pd.DataFrame, list[str]]:
    workbook_files = sorted(RAW_DIR.glob("*.xlsx"))
    if not workbook_files:
        raise FileNotFoundError("No Excel source file found. Run scripts.download_real_dataset first.")
    workbook_path = workbook_files[0]
    sheets = pd.read_excel(workbook_path, sheet_name=None, dtype=str)
    frames = []
    sheet_names = []
    for sheet_name, frame in sheets.items():
        frame = frame.copy()
        frame["source_sheet"] = sheet_name
        frames.append(frame)
        sheet_names.append(sheet_name)
    return pd.concat(frames, ignore_index=True), sheet_names


def main() -> None:
    source, sheet_names = load_source()
    raw_rows = len(source)
    source = source.rename(columns={
        "Invoice": "order_id",
        "InvoiceNo": "order_id",
        "StockCode": "product_code",
        "Description": "product_name",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "Price": "unit_price",
        "UnitPrice": "unit_price",
        "Customer ID": "customer_id",
        "CustomerID": "customer_id",
        "Country": "country",
    })
    source["order_id"] = source["order_id"].astype("string").str.strip()
    source["product_code"] = source["product_code"].astype("string").str.strip()
    source["product_name"] = source["product_name"].astype("string").str.strip()
    source["customer_id"] = source["customer_id"].map(normalized_customer_id)
    source["country"] = source["country"].fillna("Unknown").astype("string").str.strip()
    source["quantity"] = pd.to_numeric(source["quantity"], errors="coerce")
    source["unit_price"] = pd.to_numeric(source["unit_price"], errors="coerce")
    source["invoice_date"] = pd.to_datetime(source["invoice_date"], errors="coerce")

    required_valid = (
        source["order_id"].notna()
        & source["product_code"].notna()
        & source["quantity"].notna()
        & source["unit_price"].notna()
        & source["invoice_date"].notna()
        & (source["quantity"] != 0)
    )
    excluded_rows = int((~required_valid).sum())
    fact = source.loc[required_valid].copy()
    fact["order_id"] = fact["order_id"].str.replace(r"\.0$", "", regex=True)
    fact["is_return"] = fact["quantity"].lt(0) | fact["order_id"].str.upper().str.startswith("C")
    fact["gross_sales"] = fact["quantity"].mul(fact["unit_price"]).clip(lower=0).round(2)
    fact["refund_amount"] = (-fact["quantity"].mul(fact["unit_price"])).clip(lower=0).round(2)
    fact["net_sales"] = fact["gross_sales"].sub(fact["refund_amount"]).round(2)
    fact["order_date"] = fact["invoice_date"].dt.date.astype("string")
    fact["business_hour"] = fact["invoice_date"].dt.hour.astype("int16")
    fact["is_identified_customer"] = fact["customer_id"].notna().astype("int8")
    fact["source_row_id"] = range(1, len(fact) + 1)

    output_columns = [
        "source_row_id",
        "source_sheet",
        "order_id",
        "customer_id",
        "product_code",
        "product_name",
        "country",
        "invoice_date",
        "order_date",
        "business_hour",
        "quantity",
        "unit_price",
        "gross_sales",
        "refund_amount",
        "net_sales",
        "is_return",
        "is_identified_customer",
    ]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fact[output_columns].to_csv(PROCESSED_DIR / "real_transaction_fact.csv", index=False)

    quality = {
        "source_file_sheets": sheet_names,
        "raw_rows": raw_rows,
        "valid_rows": len(fact),
        "excluded_rows": excluded_rows,
        "return_rows": int(fact["is_return"].sum()),
        "rows_with_customer_id": int(fact["customer_id"].notna().sum()),
        "rows_without_customer_id": int(fact["customer_id"].isna().sum()),
        "duplicate_source_rows": int(fact.duplicated(subset=[
            "order_id", "product_code", "quantity", "invoice_date", "unit_price", "customer_id"
        ]).sum()),
        "date_min": fact["invoice_date"].min().isoformat(),
        "date_max": fact["invoice_date"].max().isoformat(),
        "gross_sales": round(float(fact["gross_sales"].sum()), 2),
        "refund_amount": round(float(fact["refund_amount"].sum()), 2),
        "net_sales": round(float(fact["net_sales"].sum()), 2),
    }
    (PROJECT_ROOT / "docs" / "real-data-quality.json").write_text(
        json.dumps(quality, indent=2), encoding="utf-8"
    )
    print(json.dumps(quality, indent=2))


if __name__ == "__main__":
    main()
