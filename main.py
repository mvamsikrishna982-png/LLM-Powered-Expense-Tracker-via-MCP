from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from dotenv import load_dotenv
import os, json, asyncpg
from contextlib import asynccontextmanager

load_dotenv()

# ── Auth ──────────────────────────────────────────────────────────────────────
try:
    DATABASE_URL = os.environ.get("DATABASE_URL")
    CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
    
except KeyError as e:
    raise RuntimeError(f"CRITICAL: Missing environment variable {e}. Check your Perfect Horizon dashboard.")


DEFAULT_CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping",
    "Entertainment", "Bills & Utilities", "Healthcare",
    "Travel", "Education", "Business", "Other"
]

# ── DB helpers ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          SERIAL PRIMARY KEY,
                date        DATE   NOT NULL,
                amount      REAL   NOT NULL,
                category    TEXT   NOT NULL,
                subcategory TEXT   DEFAULT '',
                note        TEXT   DEFAULT ''
            )
        """)
        await conn.close()
        print("DB connected and ready")
    except Exception as e:
        print(f"DB connection failed: {e}")
        raise

    yield  
    
    print("Server shutting down")

mcp = FastMCP("ExpenseTracker", lifespan=lifespan)

# Tools
@mcp.tool()
async def add_expense(date: str, amount: float, category: str,
                      subcategory: str = "", note: str = "") -> dict:
    """Add a new expense. date must be YYYY-MM-DD."""
    conn = await get_db()
    try:
        row = await conn.fetchrow(
                "INSERT INTO expenses(date, amount, category, subcategory, note)"
                " VALUES($1, $2, $3, $4, $5) RETURNING id",
                date, amount, category, subcategory, note
                )
        return {"status": "success", "id": row["id"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()
        

@mcp.tool()
async def list_expenses(start_date: str, end_date: str) -> list:
    """List expenses between start_date and end_date (YYYY-MM-DD)."""
    conn = await get_db()
    try:
        rows = await conn.fetch(
            "SELECT id, date, amount, category, subcategory, note"
            " FROM expenses"
            " WHERE date BETWEEN $1 AND $2"
            " ORDER BY date DESC, id DESC",
            start_date, end_date
        )
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

@mcp.tool()
async def summarize(start_date: str, end_date: str,
                    category: str = "") -> list:
    """Summarize spending by category between start_date and end_date."""
    query = (
        "SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count"
        " FROM expenses WHERE date BETWEEN $1 AND $2"
    )
    params = [start_date, end_date]
    if category:
        query += " AND category = $3"
        params.append(category)
    query += " GROUP BY category ORDER BY total_amount DESC"
    conn = await get_db()
    try:
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    """Delete an expense by its ID."""
    conn = await get_db()
    try:
        result = await conn.execute(
            "DELETE FROM expenses WHERE id = $1",
            expense_id
        )
        if result == "DELETE 0":
            return {"status": "error", "message": "Expense not found"}
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

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
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    # mcp.run()