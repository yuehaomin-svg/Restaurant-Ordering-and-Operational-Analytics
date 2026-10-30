from pathlib import Path

from sqlalchemy import text

from app.database import Base, SessionLocal, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    database = SessionLocal()
    try:
        sql_path = Path(__file__).resolve().parent.parent / "sql" / "analysis_views.sql"
        for statement in sql_path.read_text(encoding="utf-8").split(";"):
            if statement.strip():
                database.execute(text(statement))
        database.commit()
    finally:
        database.close()
    print("Database schema created successfully.")


if __name__ == "__main__":
    main()
