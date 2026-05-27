import asyncio
import webbrowser

from fastmcp import Client

SERVER_URL = "http://127.0.0.1:8000/mcp"

async def main():

    # Create MCP client
    client = Client(SERVER_URL)

    # Connect to server
    async with client:

        print("Connected to MCP server")

        # List available tools
        tools = await client.list_tools()

        print("\nAvailable tools:")
        for tool in tools:
            print("-", tool.name)

        print("\nOpening browser for Google login...")

        # Open login page manually
        webbrowser.open("http://127.0.0.1:8000/auth/login")

        input("\nPress ENTER after completing Google login...")

        # ------------------------------------------------------------------
        # Add expense
        # ------------------------------------------------------------------
        result = await client.call_tool(
            "add_expense",
            {
                "date": "2026-05-27",
                "amount": 250.50,
                "category": "Food & Dining",
                "subcategory": "Lunch",
                "note": "Chicken biryani"
            }
        )

        print("\nAdd Expense Result:")
        print(result)

        # ------------------------------------------------------------------
        # List expenses
        # ------------------------------------------------------------------
        result = await client.call_tool(
            "list_expenses",
            {
                "start_date": "2026-05-01",
                "end_date": "2026-05-31"
            }
        )

        print("\nExpenses:")
        print(result)

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        result = await client.call_tool(
            "summarize",
            {
                "start_date": "2026-05-01",
                "end_date": "2026-05-31"
            }
        )

        print("\nSummary:")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())