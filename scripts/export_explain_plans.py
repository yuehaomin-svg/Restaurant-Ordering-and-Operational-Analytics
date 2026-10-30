import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import text

from app.database import SessionLocal
from scripts.run_evaluation import QUERIES


def main() -> None:
    parameters = {
        "start_at": datetime.now() - timedelta(days=40),
        "end_at": datetime.now() + timedelta(days=1),
    }
    plans = {}
    database = SessionLocal()
    try:
        for query_name, query in QUERIES.items():
            row = database.execute(text(f"EXPLAIN FORMAT=JSON {query}"), parameters).one()
            plans[query_name] = json.loads(row[0])
    finally:
        database.close()
    output_path = Path(__file__).resolve().parent.parent / "docs" / "explain_plans.json"
    output_path.write_text(json.dumps(plans, indent=2), encoding="utf-8")
    print(f"Wrote {len(plans)} query plans.")


if __name__ == "__main__":
    main()
