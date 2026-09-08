"""
database.py
------------
Handles the SQLAlchemy connection to MySQL and provides:

1. A reusable database session (get_db).
2. A text description of the database schema, which is fed to the AI
   model so it knows exactly which tables/columns it is allowed to use.
3. A helper function to actually run a validated SQL SELECT query and
   return the results as a list of dictionaries.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from config import DATABASE_URL

# ---------------------------------------------------------------------------
# ENGINE + SESSION SETUP
# ---------------------------------------------------------------------------
# The engine manages the actual connection pool to MySQL.
# pool_pre_ping=True automatically checks the connection is alive before
# using it, which avoids "MySQL server has gone away" errors.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory that creates new database sessions when called.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function used by FastAPI routes to get a database session.
    Automatically closes the session once the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection():
    """
    Tries to open a simple connection to MySQL.
    Returns (True, None) on success or (False, "error message") on failure.
    This is used to give a clear, human-readable error instead of a crash.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# SCHEMA DESCRIPTION (used inside the AI prompt)
# ---------------------------------------------------------------------------
# This is a plain-text description of the library_db schema.
# It is intentionally hard-coded (rather than read dynamically from MySQL)
# to keep this beginner-friendly project simple and predictable.
#
# IMPORTANT: If you change the schema in database/create_database.sql,
# update this description to match!
DATABASE_SCHEMA = """
Table: categories
  - category_id (INT, PRIMARY KEY)
  - category_name (VARCHAR)

Table: books
  - book_id (INT, PRIMARY KEY)
  - title (VARCHAR)
  - author (VARCHAR)
  - category_id (INT, FOREIGN KEY -> categories.category_id)
  - isbn (VARCHAR)
  - published_year (INT)
  - total_copies (INT)
  - available_copies (INT)

Table: members
  - member_id (INT, PRIMARY KEY)
  - name (VARCHAR)
  - email (VARCHAR)
  - phone (VARCHAR)
  - membership_date (DATE)

Table: borrow_records
  - record_id (INT, PRIMARY KEY)
  - book_id (INT, FOREIGN KEY -> books.book_id)
  - member_id (INT, FOREIGN KEY -> members.member_id)
  - borrow_date (DATE)
  - due_date (DATE)
  - return_date (DATE, NULL if not yet returned)
  - status (VARCHAR: 'borrowed' or 'returned')
"""


def run_select_query(db, sql_query: str):
    """
    Executes an already-validated SELECT query and returns the results
    as a list of dictionaries (so it can be easily converted to JSON).

    Parameters:
        db (Session): an active SQLAlchemy session (from get_db)
        sql_query (str): the SQL SELECT statement to run

    Returns:
        (success: bool, data_or_error)
        - If success is True, data_or_error is a list of row dictionaries.
        - If success is False, data_or_error is a human-readable error string.
    """
    try:
        result = db.execute(text(sql_query))
        # result.keys() gives column names; row._mapping gives a dict-like row
        rows = [dict(row._mapping) for row in result]
        return True, rows
    except SQLAlchemyError as e:
        # Return a clean, readable error message instead of the full traceback
        return False, f"SQL execution error: {str(e.__cause__ or e)}"