"""
sql_validator.py
-----------------
Security module that checks AI-generated SQL before it is ever executed.

Rules enforced:
1. The query must be a SELECT statement (read-only).
2. The query must NOT contain any dangerous keywords such as
   INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE,
   GRANT, or REVOKE — even if they appear inside a subquery or comment.
3. The query must not contain multiple statements separated by ';'
   (this prevents "SELECT ...; DROP TABLE ..." style injection).
"""

import re

# Keywords that must NEVER appear in a query we execute.
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
    "MERGE", "CALL", "LOAD_FILE", "INTO OUTFILE", "INTO DUMPFILE",
]


def validate_sql(sql_query: str):
    """
    Validates that the given SQL string is a safe, read-only SELECT query.

    Parameters:
        sql_query (str): the raw SQL text produced by the AI model.

    Returns:
        (is_valid: bool, message: str)
        - is_valid=True means the query is safe to run.
        - is_valid=False means it was rejected; 'message' explains why.
    """
    if not sql_query or not sql_query.strip():
        return False, "Generated SQL is empty."

    cleaned = sql_query.strip()

    # Remove a trailing semicolon (a single trailing ';' is fine),
    # but reject if there is a semicolon followed by more content
    # (that would mean multiple stacked statements).
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    if ";" in cleaned:
        return False, "Multiple SQL statements are not allowed."

    # The query must start with SELECT (case-insensitive).
    if not re.match(r"^\s*SELECT\b", cleaned, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."

    # Check for any forbidden keyword anywhere in the query.
    upper_query = cleaned.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        # \b ensures we match whole words only (e.g. not match 'CREATED_AT')
        if re.search(r"\b" + re.escape(keyword) + r"\b", upper_query):
            return False, f"Query contains a forbidden keyword: {keyword}"

    return True, "Valid SELECT query."