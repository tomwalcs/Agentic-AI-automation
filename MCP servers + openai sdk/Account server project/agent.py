# agent.py  ──────────────────────────────────────────────────────────────────
"""
Tiny demo client that talks to the *accounts_server* MCP.

• Connects via stdio using the legacy `MCPClient` helper (only present in
  mcp ≤ 1.9.2).
• Asks one natural-language question, prints the agent’s reply, then exits.
"""

from __future__ import annotations

import asyncio, json, os, sys, pathlib
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, Tool, OpenAIChatCompletionsModel
from mcp.client import MCPClient          
load_dotenv()                              
##############################################################################
# 1) Build a helper that calls the accounts MCP tool over stdio              #
##############################################################################

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent

async def make_accounts_tool() -> Tool:
    """
    Returns a Tool that exposes *get_balance* by forwarding calls to the
    already-running accounts_server (stdio).
    """
    # Attach to the existing server (**do not** spawn another copy).
    client = MCPClient(stdin=sys.stdin, stdout=sys.stdout)

    async def get_balance(name: str) -> float:
        return await client.call("get_balance", name=name)

    return Tool(
        tool_name="GetBalance",
        tool_description="Return the cash balance for the given account holder.",
        coroutine=get_balance,
    )

##############################################################################
# 2) Build the agent                                                          #
##############################################################################

async def make_agent() -> Agent:
    openai_client = AsyncOpenAI()           # uses key from .env
    model = OpenAIChatCompletionsModel("gpt-4o-mini", openai_client=openai_client)

    balance_tool = await make_accounts_tool()

    return Agent(
        name="AccountAssistant",
        instructions=(
            "You are a helpful finance assistant. "
            "Answer the user’s questions by calling the GetBalance tool when helpful."
        ),
        model=model,
        tools=[balance_tool],
    )

##############################################################################
# 3) Run a single round-trip                                                 #
##############################################################################

async def main() -> None:
    agent = await make_agent()
    question = "What’s Alice’s current cash balance?"

    print(f"► user: {question}")
    result = await Runner.run(agent, question, max_turns=3)

    # `Runner.run` (agents 0.0.19) returns a dict-like RunResult whose
    # *messages* list always ends with the assistant’s reply:
    assistant_reply: str = result["messages"][-1]["content"]
    print(f"◄ assistant: {assistant_reply}")

if __name__ == "__main__":
    asyncio.run(main())
