"""main.py — minimal bootstrap for a single‑trader run

* Changes the working directory to the project root on WSL
  (``/mnt/c/Users/twalciszewski/Agentic AI projects/MCP servers + openai sdk/Equity traders``).
* Ensures a SafeChildWatcher is attached so `asyncio.create_subprocess_exec`
  works under Linux/WSL.
* Launches **one** trader (Tom) once, then prints the updated account.
"""

###############################################################################
# Std‑lib imports                                                             #
###############################################################################
from __future__ import annotations
import asyncio, os, sys, platform
from pathlib import Path

###############################################################################
# Project paths                                                               #
###############################################################################
PROJECT_ROOT = Path(
    "/mnt/c/Users/twalciszewski/Agentic AI projects/MCP servers + openai sdk/Equity traders"
)
LEGACY_DIR = PROJECT_ROOT  

###############################################################################
# In‑house imports                                                            #
###############################################################################
from traders import Trader
from account_client import read_accounts_resource

###############################################################################
# Helpers                                                                     #
###############################################################################

def prepare_env() -> None:
    """Change cwd and prepend project dir to $PATH for legacy MCP scripts."""
    os.chdir(LEGACY_DIR)
    os.environ["PATH"] = f"{LEGACY_DIR}:{os.environ.get('PATH', '')}"


def ensure_child_watcher() -> None:
    """Attach a SafeChildWatcher so subprocesses run under asyncio (WSL)."""
    if sys.platform.startswith("linux") and platform.system() != "Windows":
        from asyncio.unix_events import SafeChildWatcher

        watcher = SafeChildWatcher()
        watcher.attach_loop(asyncio.get_running_loop())
        asyncio.get_event_loop_policy().set_child_watcher(watcher)

###############################################################################
# Async main                                                                  #
###############################################################################
async def main() -> None:
    prepare_env()
    ensure_child_watcher()

    trader = Trader("Tom")
    # `Trader.run()` was removed; use the traced helper instead
    await trader.run_with_trace()  # one autonomous session)  # one autonomous session

    updated = await read_accounts_resource("Tom")
    print("\nUpdated account for Tom:\n", updated)

###############################################################################
# Entry‑point                                                                 #
###############################################################################
if __name__ == "__main__":
    asyncio.run(main())
