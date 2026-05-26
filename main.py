from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.dependencies import get_access_token
from dotenv import load_dotenv
import os, json, sqlite3, aiosqlite

load_dotenv()

# ── Auth ──────────────────────────────────────────────────────────────────────
auth = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url=os.environ["BASE_URL"],
)
mcp = FastMCP("ExpenseTracker", auth=auth)

# ── DB path (use a mounted volume on Railway/Render, not /tmp) ────────────────
DB_PATH = os.environ.get("DB_PATH", "expenses.db")

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

DEFAULT_CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping",
    "Entertainment", "Bills & Utilities", "Healthcare",
    "Travel", "Education", "Business", "Other"
]

# ── Schema init ───────────────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                subcategory TEXT    DEFAULT '',
                note        TEXT    DEFAULT ''
            )
        """)
        # Index makes per-user queries fast even with 100k+ rows
        c.execute("CREATE INDEX IF NOT EXISTS idx_user ON expenses(user_id)")
    print(f"DB ready at {DB_PATH}")

init_db()

# ── Helper ────────────────────────────────────────────────────────────────────
def current_user() -> str:
    """Extract a stable user identifier from the validated OAuth token."""
    token = get_access_token()
    # client_id is the Google 'sub' — stable, unique per Google account
    return token.client_id

# ── Tools ─────────────────────────────────────────────────────────────────────
@mcp.tool()
async def add_expense(date: str, amount: float, category: str,
                      subcategory: str = "", note: str = "") -> dict:
    """Add a new expense. date must be YYYY-MM-DD."""
    user_id = current_user()
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(
            "INSERT INTO expenses(user_id,date,amount,category,subcategory,note)"
            " VALUES (?,?,?,?,?,?)",
            (user_id, date, amount, category, subcategory, note),
        )
        await c.commit()
        return {"status": "success", "id": cur.lastrowid}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str) -> list:
    """List your expenses between start_date and end_date (YYYY-MM-DD, inclusive)."""
    user_id = current_user()
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(
            "SELECT id,date,amount,category,subcategory,note FROM expenses"
            " WHERE user_id=? AND date BETWEEN ? AND ?"
            " ORDER BY date DESC, id DESC",
            (user_id, start_date, end_date),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in await cur.fetchall()]

@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = "") -> list:
    """Summarize your spending by category between start_date and end_date."""
    user_id = current_user()
    query = (
        "SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count"
        " FROM expenses WHERE user_id=? AND date BETWEEN ? AND ?"
    )
    params: list = [user_id, start_date, end_date]
    if category:
        query += " AND category=?"
        params.append(category)
    query += " GROUP BY category ORDER BY total_amount DESC"
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in await cur.fetchall()]

@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    """Delete one of your expenses by its ID."""
    user_id = current_user()
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(
            "DELETE FROM expenses WHERE id=? AND user_id=?",  # user_id guard!
            (expense_id, user_id),
        )
        await c.commit()
        if cur.rowcount == 0:
            return {"status": "error", "message": "Expense not found or not yours"}
        return {"status": "success"}

# ── Resource ──────────────────────────────────────────────────────────────────
@mcp.resource("expense:///categories", mime_type="application/json")
def categories() -> str:
    try:
        with open(CATEGORIES_PATH, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({"categories": DEFAULT_CATEGORIES}, indent=2)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    mcp.run()