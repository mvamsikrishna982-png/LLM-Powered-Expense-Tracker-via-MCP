from fastmcp import FastMCP
import random
mcp = FastMCP('hello-server')


@mcp.tool()
def HelloWorld(name:str):
    """This function says special Hello to the user"""
    return f'{name} Suprise MF'

@mcp.tool()
def RollADie(seed:int = 3):
    """This function roll a die and returns the output"""
    return random.randint(1,6)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

# uv run fastmcp dev inspector main.py:mcp  -> for test
# uv run fastmcp run .\main.py  -> for test
# uv run cc