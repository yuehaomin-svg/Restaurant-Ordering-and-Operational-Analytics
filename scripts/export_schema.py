from pathlib import Path

from sqlalchemy import text

from app.database import Base, SessionLocal
from app.models import Base as ModelBase


def main() -> None:
    output_path = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    statements = [
        "-- Generated from the SQLAlchemy schema.",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS=0;",
    ]
    database = SessionLocal()
    try:
        for table_name in sorted(ModelBase.metadata.tables):
            row = database.execute(text(f"SHOW CREATE TABLE `{table_name}`")).one()
            statements.extend(["", f"-- {table_name}", f"{row[1]};"])
    finally:
        database.close()
    statements.extend(["", "SET FOREIGN_KEY_CHECKS=1;", ""])
    output_path.write_text("\n".join(statements), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
