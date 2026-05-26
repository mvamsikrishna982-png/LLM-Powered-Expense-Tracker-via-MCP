from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from dotenv import load_dotenv
import os
import sqlite3
import aiosqlite

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(DATA_DIR, "categories.json")

# auth = GoogleProvider(
#     client_id=os.environ["GOOGLE_CLIENT_ID"],
#     client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
#     base_url=os.environ.get("BASE_URL", "http://localhost:8000/mcp")  
# )

# mcp = FastMCP("ExpenseTracker", auth=auth)  # ← only ONE mcp instance
mcp = FastMCP("ExpenseTracker")  

print(f"Database path: {DB_PATH}")

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

init_db()

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await c.commit()
            return {"status": "success", "id": expense_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "SELECT id, date, amount, category, subcategory, note FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC, id DESC",
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
                FROM expenses WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " GROUP BY category ORDER BY total_amount DESC"
            cur = await c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    default_categories = {
        "categories": [
            "Food & Dining", "Transportation", "Shopping",
            "Entertainment", "Bills & Utilities", "Healthcare",
            "Travel", "Education", "Business", "Other"
        ]
    }
    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        import json
        return json.dumps(default_categories, indent=2)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
    # mcp.run()