"""
traders.py – orchestrates the Researcher-as-tool plus the Trader agent.
Key points:
• tolerant import of  researcher_mcp_server_params
• MCPServerStdio gets a longer start-up timeout (20 s, configured in mcp_params)
"""

from __future__ import annotations
import asyncio, contextlib, json, os
from contextlib import AsyncExitStack

from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from agents.mcp import MCPServerStdio
from account_client import read_accounts_resource, read_strategy_resource
from tracers import make_trace_id
from templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(override=True)

# ──────────────────────────────────────────────────────────────────────────────
# 1.  Import the *two* param lists, but tolerate a missing researcher list
# ──────────────────────────────────────────────────────────────────────────────
try:
    from mcp_params import (
        trader_mcp_server_params,
        researcher_mcp_server_params,
    )
except ImportError:                      
    from mcp_params import trader_mcp_server_params
    researcher_mcp_server_params = []

# ──────────────────────────────────────────────────────────────────────────────
# 2.  Model plumbing helpers  (unchanged – shortened here for brevity)
# ──────────────────────────────────────────────────────────────────────────────


def get_model(model_name: str):
    # You may want to adjust this logic to match your needs
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=AsyncOpenAI())
    else:
        return model_name

# ──────────────────────────────────────────────────────────────────────────────
# 3.  Trader class
# ──────────────────────────────────────────────────────────────────────────────
MAX_TURNS = 30

class Trader:
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.do_trade = True          # flip-flops between trade & rebalance

    # ------------------------------------------------------------ helpers ----
    async def _researcher_tool(self, mcp_servers) -> Tool:
        researcher = Agent(
            name="Researcher",
            instructions=researcher_instructions(),
            model=get_model(self.model_name),
            mcp_servers=mcp_servers,
        )
        return researcher.as_tool("Researcher", research_tool())

    async def _make_agent(self, trader_mcp, researcher_mcp) -> Agent:
        tool = await self._researcher_tool(researcher_mcp)
        return Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            tools=[tool],
            mcp_servers=trader_mcp,
        )

    async def _account_snapshot(self) -> tuple[str, str]:
        """Return (account_json, strategy_text)."""
        acc   = await read_accounts_resource(self.name)
        acc_j = json.loads(acc)
        acc_j.pop("portfolio_value_time_series", None)
        strategy = await read_strategy_resource(self.name)
        return json.dumps(acc_j), strategy

    # ------------------------------------------------------------ main loop --
    async def _session(self, trader_mcp, researcher_mcp):
        agent = await self._make_agent(trader_mcp, researcher_mcp)
        account_json, strat = await self._account_snapshot()
        initial_msg = (
            trade_message(self.name, strat, account_json)
            if self.do_trade
            else rebalance_message(self.name, strat, account_json)
        )
        await Runner.run(agent, initial_msg, max_turns=MAX_TURNS)
        self.do_trade = not self.do_trade        # flip at the very end

    async def run_with_mcp_servers(self):
        """Spin up all required MCP servers (with 20 s timeout each)."""
        async with AsyncExitStack() as stack:
            trader_mcp = [
                await stack.enter_async_context(MCPServerStdio(p))
                for p in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack_r:
                researcher_mcp = [
                    await stack_r.enter_async_context(MCPServerStdio(p))
                    for p in researcher_mcp_server_params
                ]
                await self._session(trader_mcp, researcher_mcp)

    async def run_with_trace(self):
        trace_id = make_trace_id(self.name.lower())
        mode     = "trading" if self.do_trade else "rebalancing"
        with trace(f"{self.name}-{mode}", trace_id=trace_id):
            await self.run_with_mcp_servers()
