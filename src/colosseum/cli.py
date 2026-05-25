"""CLI for Agent Colosseum — run simulations from the terminal."""

from __future__ import annotations

import argparse
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from colosseum.scenarios import ALL_SCENARIOS

console = Console()


def _get_client(mock: bool = False):
    """Get the appropriate client based on mode."""
    if mock or not os.environ.get("CRUSOE_API_KEY"):
        from colosseum.mock_client import MockCrusoeClient
        return MockCrusoeClient()
    from colosseum.crusoe_client import CrusoeClient
    return CrusoeClient()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="colosseum",
        description="Agent Colosseum — simulate multi-agent environments with Nvidia Nemotron on Crusoe Cloud",
    )
    parser.add_argument("--mock", action="store_true", help="Run in offline demo mode (no API key needed)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List available scenarios")

    # run
    run_parser = sub.add_parser("run", help="Run a simulation")
    run_parser.add_argument("scenario", help="Scenario name or path to JSON config")
    run_parser.add_argument("--analyze", "-a", action="store_true", help="Show AI analysis after run")

    # design
    design_parser = sub.add_parser("design", help="Design a custom experiment with AI assistance")
    design_parser.add_argument("task", nargs="+", help="Task description")
    design_parser.add_argument("--agents", "-n", type=int, default=4)
    design_parser.add_argument("--desc", "-d", default="")

    # demo
    sub.add_parser("demo", help="Run the full offline demo showcase")

    return parser


def cmd_list() -> None:
    table = Table(title="Available Scenarios", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Agents")
    table.add_column("Description")
    for name, cfg in ALL_SCENARIOS.items():
        table.add_row(name, str(len(cfg.agents)), cfg.description)
    console.print(table)


def cmd_run(args: argparse.Namespace) -> None:
    from colosseum.simulation.orchestrator import Orchestrator

    client = _get_client(mock=args.mock)
    orch = Orchestrator(client=client)

    if args.scenario in ALL_SCENARIOS:
        config = ALL_SCENARIOS[args.scenario]
        console.print(f"\n[bold]Running scenario:[/] {config.name}")
    else:
        console.print(f"[red]Unknown scenario:[/] {args.scenario}")
        console.print("Use 'colosseum list' to see available scenarios.")
        sys.exit(1)

    console.print(f"  Agents: {len(config.agents)} | Max steps: {config.max_steps}")
    console.print(f"  Task: {config.task}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Running simulation...", total=config.max_steps)

        def update(step: int, total: int) -> None:
            progress.update(task_id, completed=step, description=f"Step {step}/{total}...")

        result = orch.run_experiment(config, progress_callback=update)

    console.print(f"\n[bold green]Simulation complete.[/] {result.total_steps} steps run.")

    stats_table = Table(title="Agent Performance", box=box.ROUNDED)
    stats_table.add_column("Agent")
    stats_table.add_column("Role")
    stats_table.add_column("Steps")
    stats_table.add_column("State")
    for name, stats in result.agent_stats.items():
        stats_table.add_row(
            name, stats.get("role", "-"),
            str(stats.get("steps_taken", "-")), stats.get("state", "-"),
        )
    console.print(stats_table)

    console.print("\n[bold]Last actions:[/]")
    for action in result.steps[-1][-6:]:
        console.print(f"  [{action.action_type}][/] [cyan]{action.agent_name}[/]: {action.content[:120]}")

    if result.anomalies:
        console.print("\n[bold yellow]Anomalies:[/]")
        for a in result.anomalies:
            console.print(f"  - {a}")

    if args.analyze:
        console.print("\n[bold]AI Analysis:[/]")
        with console.status("Analyzing results..."):
            analysis = orch.analyze_results(result)
        console.print(Panel(analysis, title="Analysis"))

    console.print(f"\n[dim]API calls: {orch.stats['calls']} | "
                  f"Avg latency: {orch.stats.get('avg_latency_ms', 0)}ms[/]")


def cmd_design(args: argparse.Namespace) -> None:
    from colosseum.simulation.orchestrator import Orchestrator

    client = _get_client(mock=args.mock)
    orch = Orchestrator(client=client)
    task_text = " ".join(args.task)

    console.print(f"\n[bold]Designing experiment for:[/] {task_text}")
    with console.status("Orchestrator designing agent team..."):
        config = orch.design_experiment(
            task=task_text,
            description=args.desc or task_text,
            num_agents=args.agents,
        )

    console.print(f"\n[bold green]Designed:[/] {config.name}")
    console.print(f"  Environment: {config.environment_prompt[:200]}...")
    agents_table = Table(title="Agents", box=box.ROUNDED)
    agents_table.add_column("Name")
    agents_table.add_column("Role")
    agents_table.add_column("Personality")
    for ag in config.agents:
        agents_table.add_row(ag.name, ag.role.value, ag.personality[:60])
    console.print(agents_table)

    console.print("\n[bold]Running experiment...[/]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Simulating...", total=config.max_steps)

        def update(step: int, total: int) -> None:
            progress.update(task_id, completed=step, description=f"Step {step}/{total}...")

        result = orch.run_experiment(config, progress_callback=update)

    with console.status("Analyzing results..."):
        analysis = orch.analyze_results(result)
    console.print(Panel(analysis, title="Orchestrator Analysis"))


def cmd_demo(args: argparse.Namespace) -> None:
    """Run the full offline demo showcase."""
    from colosseum.scenarios import DEBATE_SOCIETY, CRISIS_RESPONSE, STARTUP_BRAINSTORM
    from colosseum.mock_client import MockCrusoeClient
    from colosseum.simulation.orchestrator import Orchestrator

    client = MockCrusoeClient(latency_range=(0.2, 0.6))
    orch = Orchestrator(client=client)

    console.print(
        Panel.fit(
            "[bold cyan]Agent Colosseum — Demo Showcase[/]\n"
            "Multi-agent simulation with Nvidia Nemotron on Crusoe Cloud\n"
            "DevNetwork AI+ML Hackathon 2026",
            border_style="cyan",
        )
    )

    for name, cfg, desc in [
        ("debate", DEBATE_SOCIETY, "4 agents debate AI persistent memory"),
        ("crisis", CRISIS_RESPONSE, "4 agents coordinate data center recovery"),
        ("startup", STARTUP_BRAINSTORM, "4 agents brainstorm AI startup ideas"),
    ]:
        console.print(f"\n[bold yellow]▶[/] [bold]{name}[/]: {desc}")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_id = progress.add_task(f"Running {name}...", total=cfg.max_steps)
            def update(step: int, total: int) -> None:
                progress.update(task_id, completed=step, description=f"Step {step}/{total}...")
            result = orch.run_experiment(cfg, progress_callback=update)

        for action in result.steps[-1][:4]:
            console.print(f"  [{action.action_type}][/] [cyan]{action.agent_name}[/]: {action.content[:120]}")

    console.print(f"\n[bold green]Demo complete.[/] {orch.stats['experiments_run']} experiments, "
                  f"{orch.stats['calls']} API calls")

    if len(orch.results) > 1:
        with console.status("Comparing experiments..."):
            comparison = orch.compare_experiments()
        console.print(Panel(comparison, title="Cross-Experiment Comparison", border_style="magenta"))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        console.print(
            Panel.fit(
                "[bold cyan]Agent Colosseum[/]\n"
                "Simulate multi-agent environments with Nvidia Nemotron on Crusoe Cloud\n\n"
                "Commands: list | run | design | demo",
                title="Welcome",
            )
        )
        parser.print_help()
        return

    if args.command == "list":
        cmd_list()
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "design":
        cmd_design(args)
    elif args.command == "demo":
        cmd_demo(args)


if __name__ == "__main__":
    main()
