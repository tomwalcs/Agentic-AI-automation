from __future__ import annotations
import importlib
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("accounts_server")

# --------------------------------------------------------------------- #
#  Tiny helper that loads Account the *first* time we actually need it  #
# --------------------------------------------------------------------- #
def _Account():
    global Account                 # type: ignore  # injected at runtime
    try:
        return Account             # already imported
    except NameError:
        Account = importlib.import_module("accounts").Account
        return Account


# ---------------------------  TOOLS  --------------------------------- #

@mcp.tool()
async def get_balance(name: str) -> float:
    """Return the cash balance of *name*."""
    return _Account().get(name).balance


@mcp.tool()
async def get_holdings(name: str) -> dict[str, int]:
    """Return the share-count dict for *name*."""
    return _Account().get(name).holdings


@mcp.tool()
async def buy_shares(
    name: str, symbol: str, quantity: int, rationale: str
) -> float:
    """Buy *quantity* shares of *symbol* for *name*."""
    return _Account().get(name).buy_shares(symbol, quantity, rationale)


@mcp.tool()
async def sell_shares(
    name: str, symbol: str, quantity: int, rationale: str
) -> float:
    """Sell *quantity* shares of *symbol* for *name*."""
    return _Account().get(name).sell_shares(symbol, quantity, rationale)


@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """Update *name*’s long-term investment strategy."""
    return _Account().get(name).change_strategy(strategy)


# --------------------------  RESOURCES  ------------------------------ #

@mcp.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    return _Account().get(name.lower()).report()


@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    return _Account().get(name.lower()).get_strategy()


# ---------------------------  MAIN  ---------------------------------- #
if __name__ == "__main__":
    # No long work above –  handshake goes out instantly
    mcp.run(transport="stdio")
