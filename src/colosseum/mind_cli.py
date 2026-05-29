"""`mind` — a single-mind chat REPL. You talk to ONE mind (Nemotron); the slots are inside it.

This is the WI-5 CLI: no host/model picker, no compare-hosts, no chaos, no scenarios (that was
the rejected `cli.py`). It drives the SAME `Mind.respond` contract as the Streamlit app, so the
CLI and GUI are provably one product.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from colosseum.mind import Mind
from colosseum.llm import LLMClient

DEGRADED_REPLY = "My thoughts didn't converge into a reply just now — try again."


def _client(console: Console) -> LLMClient:
    # LLMClient defaults to MIND_*/NVIDIA; the slots are Crusoe models, so wire Crusoe explicitly.
    try:
        return LLMClient(api_key=os.environ["CRUSOE_API_KEY"],
                         base_url=os.environ["CRUSOE_BASE_URL"])
    except KeyError:
        console.print("[red]Set CRUSOE_API_KEY and CRUSOE_BASE_URL (see .env.example) "
                      "to talk to the mind.[/red]")
        sys.exit(1)


def _print_slots(console: Console, turn) -> None:
    if turn.perspectives:
        for p in turn.perspectives:
            if p.available:
                console.print(f"   [bold]· {p.label}[/bold]: {p.content}")
            else:
                console.print(f"   [dim]· {p.label}: {p.content}[/dim]")
    elif turn.blocked:
        console.print("   [dim]· (the boundary stopped this before the slots engaged)[/dim]")


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(description="Talk to the one mind (Nemotron + slotted models).")
    ap.add_argument("--show-slots", action="store_true", help="show each slot's perspective")
    ap.add_argument("--gatekeeper", action="store_true", help="show the boundary gatekeeper log")
    args = ap.parse_args()

    console = Console()
    mind = Mind(client=_client(console))
    slots = ", ".join(s.label for s in mind.active_slots)
    console.print(Panel(f"[bold]THE MIND[/bold] — Nemotron Super-120B\n"
                        f"[dim]minds inside:[/dim] {slots}\n"
                        f"[dim]Ctrl-D to leave.[/dim]", border_style="cyan"))

    history: list[dict] = []
    while True:
        try:
            msg = console.input("[bold cyan]you ›[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]…the mind rests.[/dim]")
            break
        if not msg:
            continue

        ctx = history[-8:]  # PRIOR turns only — respond() re-adds the current message itself
        with console.status("[dim]the mind is thinking…[/dim]"):
            turn = mind.respond(msg, ctx)

        if turn.blocked:
            border, tag = "yellow", " (boundary)"
        elif turn.reply == DEGRADED_REPLY:
            border, tag = "yellow", " (didn't converge)"
        else:
            border, tag = "green", ""
        console.print(Panel(turn.reply, title=f"the mind{tag}", border_style=border))

        if args.show_slots:
            _print_slots(console, turn)
        if args.gatekeeper:
            for line in turn.gatekeeper_log:
                console.print(f"   [dim]{line}[/dim]")

        history.append({"role": "user", "content": msg})        # appended AFTER respond
        history.append({"role": "assistant", "content": turn.reply})


if __name__ == "__main__":
    main()
