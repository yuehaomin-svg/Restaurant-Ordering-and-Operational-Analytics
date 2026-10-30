from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "restaurant_demo.sqlite3"

st.set_page_config(
    page_title="Restaurant Analytics Streamlit Demo",
    page_icon="🍜",
    layout="wide",
)


@st.cache_data
def load_data():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        orders = pd.read_sql_query(
            """
            SELECT o.id, o.order_no, o.status, o.total_amount, o.placed_at,
                   o.customer_id, c.name AS customer_name, t.name AS table_name
            FROM orders o
            LEFT JOIN customers c ON c.id = o.customer_id
            LEFT JOIN dining_tables t ON t.id = o.table_id
            """,
            connection,
        )
        order_items = pd.read_sql_query(
            """
            SELECT oi.order_id, oi.menu_item_id, oi.quantity, oi.unit_price,
                   oi.line_total, mi.name AS item_name, mc.name AS category_name
            FROM order_items oi
            JOIN menu_items mi ON mi.id = oi.menu_item_id
            JOIN menu_categories mc ON mc.id = mi.category_id
            """,
            connection,
        )
        refunds = pd.read_sql_query(
            """
            SELECT p.order_id, r.amount, r.reason, r.refunded_at
            FROM refunds r
            JOIN payments p ON p.id = r.payment_id
            """,
            connection,
        )
    finally:
        connection.close()

    orders["placed_at"] = pd.to_datetime(orders["placed_at"])
    orders["order_date"] = orders["placed_at"].dt.date
    orders["hour"] = orders["placed_at"].dt.hour
    refund_by_order = refunds.groupby("order_id")["amount"].sum().rename("refund_amount")
    orders = orders.join(refund_by_order, on="id").fillna({"refund_amount": 0})
    orders["refund_amount"] = pd.to_numeric(orders["refund_amount"])
    orders["net_amount"] = orders["total_amount"] - orders["refund_amount"]

    item_refund = order_items.join(
        orders.set_index("id")["refund_amount"], on="order_id", rsuffix="_order"
    )
    order_totals = orders.set_index("id")["total_amount"].replace(0, 1)
    item_refund["refund_allocation"] = (
        item_refund["line_total"] / item_refund["order_id"].map(order_totals)
    ) * item_refund["refund_amount"].fillna(0)
    item_refund["net_sales"] = item_refund["line_total"] - item_refund["refund_allocation"]
    return orders, item_refund, refunds


def money(value: float) -> str:
    return f"HK${value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def frequency_band(count: int) -> str:
    if count == 1:
        return "1 order"
    if count <= 3:
        return "2-3 orders"
    if count <= 10:
        return "4-10 orders"
    return "11+ orders"


orders, items, refunds = load_data()
if orders.empty:
    st.error("演示数据库为空，请先运行 `python -m scripts.seed_data --orders 1000 --reset`。")
    st.stop()

st.title("🍜 Restaurant Analytics Streamlit Demo")
st.caption("A browser-ready demo backed by a reproducible SQLite snapshot of 1,000 synthetic restaurant orders.")

with st.sidebar:
    st.header("Filters")
    min_date = orders["order_date"].min()
    max_date = orders["order_date"].max()
    date_range = st.date_input("Order date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    categories = ["All categories"] + sorted(items["category_name"].dropna().unique().tolist())
    category_filter = st.selectbox("Product category", categories)
    st.markdown("---")
    st.markdown("**Data source**")
    st.code("restaurant_demo.sqlite3", language="text")
    st.markdown("This is synthetic data for demonstration and analysis practice.")

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

filtered_orders = orders[(orders["order_date"] >= start_date) & (orders["order_date"] <= end_date)].copy()
filtered_items = items[items["order_id"].isin(filtered_orders["id"])].copy()
if category_filter != "All categories":
    filtered_items = filtered_items[filtered_items["category_name"] == category_filter]

gross_sales = float(filtered_orders["total_amount"].sum())
refund_amount = float(filtered_orders["refund_amount"].sum())
net_sales = gross_sales - refund_amount
order_count = int(filtered_orders["id"].nunique())
average_order_value = gross_sales / order_count if order_count else 0
refund_rate = refund_amount / gross_sales if gross_sales else 0

kpi_columns = st.columns(5)
kpi_columns[0].metric("Orders", f"{order_count:,}")
kpi_columns[1].metric("Gross sales", money(gross_sales))
kpi_columns[2].metric("Net sales", money(net_sales))
kpi_columns[3].metric("Refund rate", pct(refund_rate))
kpi_columns[4].metric("Average order value", money(average_order_value))

overview, products, orders_tab, customer_timing, notes = st.tabs(
    ["Executive Overview", "Product Strategy", "Orders", "Customer & Timing", "Data Notes"]
)

with overview:
    st.subheader("Sales trend")
    daily = (
        filtered_orders.groupby("order_date", as_index=False)
        .agg(order_count=("id", "nunique"), gross_sales=("total_amount", "sum"), refund_amount=("refund_amount", "sum"), net_amount=("net_amount", "sum"))
        .sort_values("order_date")
    )
    daily["order_date"] = daily["order_date"].astype(str)
    st.line_chart(daily.set_index("order_date")[["gross_sales", "refund_amount", "net_amount"]], height=320)
    st.caption("Refund history is kept separate from gross sales so the sales trend remains auditable.")

    st.subheader("Hourly demand")
    hourly = (
        filtered_orders.groupby("hour", as_index=False)
        .agg(order_count=("id", "nunique"), gross_sales=("total_amount", "sum"), net_amount=("net_amount", "sum"))
        .sort_values("hour")
    )
    left, right = st.columns(2)
    left.bar_chart(hourly.set_index("hour")[["order_count"]], height=280)
    right.line_chart(hourly.set_index("hour")[["net_amount"]], height=280)
    if not hourly.empty:
        peak_orders = hourly.loc[hourly["order_count"].idxmax()]
        peak_sales = hourly.loc[hourly["net_amount"].idxmax()]
        st.info(f"Orders peak at {int(peak_orders['hour'])}:00; net sales peak at {int(peak_sales['hour'])}:00.")

with products:
    st.subheader("Product performance")
    product = (
        filtered_items.groupby(["menu_item_id", "item_name", "category_name"], as_index=False)
        .agg(units_sold=("quantity", "sum"), order_count=("order_id", "nunique"), gross_sales=("line_total", "sum"), refund_allocation=("refund_allocation", "sum"), net_sales=("net_sales", "sum"))
        .sort_values("net_sales", ascending=False)
    )
    if not product.empty:
        average_units = product["units_sold"].mean()
        average_net = product["net_sales"].mean()
        product["segment"] = "Dogs"
        product.loc[(product["units_sold"] >= average_units) & (product["net_sales"] < average_net), "segment"] = "Plowhorses"
        product.loc[(product["units_sold"] < average_units) & (product["net_sales"] >= average_net), "segment"] = "Puzzles"
        product.loc[(product["units_sold"] >= average_units) & (product["net_sales"] >= average_net), "segment"] = "Stars"
        st.scatter_chart(product, x="units_sold", y="net_sales", color="segment", size="order_count", height=390)
        st.dataframe(product, width="stretch", hide_index=True)
        st.download_button("Download product summary CSV", product.to_csv(index=False).encode("utf-8-sig"), file_name="product-summary.csv")
    else:
        st.warning("No product rows match the current filters.")

with orders_tab:
    st.subheader("Order explorer")
    order_list = filtered_orders.sort_values("placed_at", ascending=False).copy()
    st.dataframe(order_list[["order_no", "table_name", "customer_name", "status", "total_amount", "refund_amount", "net_amount", "placed_at"]], width="stretch", hide_index=True)
    selected_order = st.selectbox("Inspect one order", order_list["order_no"].tolist())
    if selected_order:
        order_id = int(order_list.loc[order_list["order_no"] == selected_order, "id"].iloc[0])
        order_detail = filtered_items[filtered_items["order_id"] == order_id][["item_name", "category_name", "quantity", "unit_price", "line_total", "refund_allocation", "net_sales"]]
        st.dataframe(order_detail, width="stretch", hide_index=True)

with customer_timing:
    st.subheader("Customer repeat behavior")
    customer = (
        filtered_orders[filtered_orders["customer_id"].notna()]
        .groupby("customer_id", as_index=False)
        .agg(order_count=("id", "nunique"), gross_sales=("total_amount", "sum"), refund_amount=("refund_amount", "sum"), net_amount=("net_amount", "sum"))
    )
    identified_customers = len(customer)
    repeat_customers = int((customer["order_count"] > 1).sum())
    identified_orders = int(filtered_orders[filtered_orders["customer_id"].notna()]["id"].nunique())
    repeat_orders = int((customer.loc[customer["order_count"] > 1, "order_count"] - 1).sum()) if identified_customers else 0
    repeat_customer_rate = repeat_customers / identified_customers if identified_customers else 0
    repeat_order_rate = repeat_orders / identified_orders if identified_orders else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Identified customers", f"{identified_customers:,}")
    c2.metric("Repeat customer rate", pct(repeat_customer_rate))
    c3.metric("Repeat order rate", pct(repeat_order_rate))
    c4.metric("Repeat customers", f"{repeat_customers:,}")
    if identified_customers:
        customer["frequency_band"] = customer["order_count"].map(frequency_band)
        frequency = customer.groupby("frequency_band", as_index=False)["customer_id"].nunique().rename(columns={"customer_id": "customer_count"})
        st.bar_chart(frequency.set_index("frequency_band")[["customer_count"]], height=280)
        st.caption("Anonymous orders without customer_id are excluded from repeat calculations.")

with notes:
    st.subheader("Metric definitions")
    st.code(
        """
Gross sales = SUM(order.total_amount)
Refund amount = SUM(refund.amount)
Net sales = Gross sales - Refund amount
Refund rate = Refund amount / Gross sales
Average order value = Gross sales / completed orders
Repeat customer rate = customers with >=2 orders / identified customers
Repeat order rate = (identified orders - first orders) / identified orders
        """.strip(),
        language="text",
    )
    st.subheader("Scope and limitations")
    st.markdown(
        """
- This app uses a deterministic synthetic restaurant dataset, not live production data.
- Refunds are allocated proportionally to product line totals within each order.
- Product segments measure sales contribution, not profit, because product cost is not included.
- The Streamlit app is a presentation layer; the underlying transaction system remains available in the repository.
        """
    )
