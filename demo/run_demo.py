#!/usr/bin/env python3
"""Offline demo runner — generates a complete demo output for submission video.

Uses MockCrusoeClient for realistic, deterministic interactions without API key.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich import box

from colosseum.scenarios import ALL_SCENARIOS, DEBATE_SOCIETY, STARTUP_BRAINSTORM, CRISIS_RESPONSE
from colosseum.mock_client import MockCrusoeClient
from colosseum.simulation.orchestrator import Orchestrator

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]  Agent Colosseum[/]\n"
            "  Simulate multi-agent environments with Nvidia Nemotron on Crusoe Cloud\n\n"
            "  [dim]DevNetwork AI+ML Hackathon 2026 — Crusoe Challenge[/]",
            title="[bold white]🏛️[/]",
            border_style="cyan",
        )
    )


def demo_scenario(name: str, config, client: MockCrusoeClient, orch: Orchestrator | None = None, analyze: bool = True):
    """Run a single scenario demonstration. Returns orchestrator for cross-comparison."""
    console.print(f"\n[bold yellow]▶[/] Running scenario: [bold]{name}[/]")
    console.print(f"  Task: {config.task}")
    console.print(f"  Agents: {len(config.agents)} | Max steps: {config.max_steps}")

    if orch is None:
        orch = Orchestrator(client=client)

    # Show agent lineup
    table = Table(title="Agent Lineup", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Role")
    table.add_column("Personality", style="italic")
    table.add_column("Model")
    for ag in config.agents:
        table.add_row(ag.name, ag.role.value, ag.personality[:40], "Nano-30B")
    console.print(table)

    # Run simulation with progress
    console.print("\n[bold]Simulating...[/]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Agents interacting via Crusoe/Nemotron...", total=config.max_steps)

        def update(step: int, total: int) -> None:
            progress.update(task_id, completed=step, description=f"Step {step}/{total}...")

        start = time.time()
        result = orch.run_experiment(config, progress_callback=update)
        elapsed = time.time() - start

    console.print(f"\n[bold green]✅ Complete[/] in {elapsed:.1f}s — {result.total_steps} steps")

    # Agent stats
    stats_table = Table(title="Agent Performance", box=box.ROUNDED)
    stats_table.add_column("Agent", style="cyan")
    stats_table.add_column("Role")
    stats_table.add_column("Steps")
    stats_table.add_column("State")
    for agent_name, stats in result.agent_stats.items():
        stats_table.add_row(
            agent_name,
            stats.get("role", "-"),
            str(stats.get("steps_taken", "-")),
            stats.get("state", "-"),
        )
    console.print(stats_table)

    # Show interaction timeline
    console.print("\n[bold]Interaction Timeline:[/]")
    for step_idx, step_actions in enumerate(result.steps):
        step_color = "dim" if step_idx > 3 else "white"
        console.print(f"\n  [{step_color}]── Step {step_idx + 1} ──[/]")
        for action in step_actions:
            icons = {
                "think": "💭", "speak": "💬", "tool_call": "🔧",
                "decide": "✅", "delegate": "👋", "ask": "❓", "error": "❌",
            }
            icon = icons.get(action.action_type, "•")
            style = {
                "speak": "green", "decide": "cyan", "error": "red", "think": "dim",
            }.get(action.action_type, "")
            console.print(f"  {icon} [{style}]{action.agent_name}[/] [{action.action_type}]: {action.content[:150]}")

    if result.anomalies:
        console.print("\n[bold yellow]⚠ Anomalies:[/]")
        for a in result.anomalies:
            console.print(f"  - {a}")

    # Orchestrator analysis
    if analyze:
        console.print("\n[bold]🧠 Orchestrator Analysis (Nemotron Super-120B):[/]")
        with console.status("Analyzing results..."):
            analysis = orch.analyze_results(result)
        console.print(Panel(analysis, title="Analysis", border_style="blue"))

    return orch


def main():
    print_banner()

    client = MockCrusoeClient(latency_range=(0.2, 0.8))
    orch = Orchestrator(client=client)

    console.print("\n[bold]Part 1: Debate Society[/] — 4 agents debate AI persistent memory")
    console.print("─" * 60)
    demo_scenario("debate", DEBATE_SOCIETY, client, orch=orch)

    console.print("\n\n[bold]Part 2: Crisis Response[/] — 4 agents coordinate data center recovery")
    console.print("─" * 60)
    demo_scenario("crisis", CRISIS_RESPONSE, client, orch=orch)

    console.print("\n\n[bold]Part 3: Startup Brainstorm[/] — 4 agents ideate and evaluate AI startups")
    console.print("─" * 60)
    demo_scenario("startup", STARTUP_BRAINSTORM, client, orch=orch)

    # Cross-experiment comparison
    console.print("\n\n[bold]Cross-Experiment Comparison[/]")
    console.print("─" * 60)

    with console.status("Comparing experiments..."):
        comparison = orch.compare_experiments()
    console.print(Panel(comparison, title="Cross-Experiment Comparison", border_style="magenta"))

    # Final summary
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Agent Colosseum[/]\n\n"
        "Built with Nvidia Nemotron (Super-120B + Nano-30B) on Crusoe Cloud Managed Inference\n"
        "OpenAI-compatible API • Multi-agent simulation • AI-designed experiments\n\n"
        "[dim]github.com/Alex_Sorrell_IT/agent-colosseum[/]",
        title="[bold white]🏛️ Thanks for watching![/]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
