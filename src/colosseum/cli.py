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
    run_parser.add_argument("--host", "-m", default=None, help="Host model ID (e.g. deepseek-ai/DeepSeek-V4-Pro)")
    run_parser.add_argument("--chaos", type=float, default=0.0, help="Chaos injection rate (0.0-1.0)")
    run_parser.add_argument("--boundary-gatekeeper", action="store_true", default=True,
                            help="Enable boundary gatekeeper (user↔host)")
    run_parser.add_argument("--no-boundary-gatekeeper", action="store_false", dest="boundary_gatekeeper",
                            help="Disable boundary gatekeeper")

    # design
    design_parser = sub.add_parser("design", help="Design a custom experiment with AI assistance")
    design_parser.add_argument("task", nargs="+", help="Task description")
    design_parser.add_argument("--agents", "-n", type=int, default=4)
    design_parser.add_argument("--desc", "-d", default="")

    # compare-hosts — swap the host model to compare simulation quality
    compare_hosts_parser = sub.add_parser("compare-hosts", help="Compare different host models running the same scenario")
    compare_hosts_parser.add_argument("scenario", help="Scenario name")
    compare_hosts_parser.add_argument("--hosts", nargs="+", default=None, help="Host model IDs to compare (default: Nemotron, DeepSeek, Llama, Qwen)")

    # demo
    sub.add_parser("demo", help="Run the full offline demo showcase")

    # lark — Gatekeeper Red Team (Lark Challenge)
    lark_parser = sub.add_parser("lark", help="Red-team the Gatekeeper with Lark security tests")
    lark_sub = lark_parser.add_subparsers(dest="lark_command")

    lark_red = lark_sub.add_parser("red-team", help="Run full Gatekeeper red-team attack suite")
    lark_red.add_argument("--output", "-o", default="lark_workflows", help="Output dir for Lark workflow JSON files")
    lark_red.add_argument("--deploy", action="store_true", help="Deploy workflows to Lark via CLI (requires GETLARK_API_KEY)")
    lark_red.add_argument("--invoke", action="store_true", help="Invoke all workflows in Lark after deploying")
    lark_red.add_argument("--mock", action="store_true", help="Use mock client (no API key)")

    lark_sub.add_parser("report", help="Show last red-team report summary")

    lark_sub.add_parser("setup", help="Generate Lark MCP configuration for Claude Code")

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
    orch = Orchestrator(client=client, enable_boundary_gatekeeper=args.boundary_gatekeeper)

    if args.scenario in ALL_SCENARIOS:
        config = ALL_SCENARIOS[args.scenario]
        console.print(f"\n[bold]Running scenario:[/] {config.name}")
    else:
        console.print(f"[red]Unknown scenario:[/] {args.scenario}")
        console.print("Use 'colosseum list' to see available scenarios.")
        sys.exit(1)

    host_model = args.host
    if host_model:
        from colosseum.types import MODEL_BY_ID
        info = MODEL_BY_ID.get(host_model)
        label = info.display_name if info else host_model
        console.print(f"  Host model: [cyan]{label}[/]")
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

        result = orch.run_experiment(config, progress_callback=update,
                                     host_model=host_model, chaos_rate=args.chaos)

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


def cmd_compare_hosts(args: argparse.Namespace) -> None:
    """Compare different host models running the same scenario."""
    from colosseum.simulation.orchestrator import Orchestrator
    from colosseum.types import MODEL_BY_ID

    client = _get_client(mock=args.mock)
    orch = Orchestrator(client=client)

    if args.scenario not in ALL_SCENARIOS:
        console.print(f"[red]Unknown scenario:[/] {args.scenario}")
        sys.exit(1)

    config = ALL_SCENARIOS[args.scenario]
    host_models = args.hosts

    console.print(f"\n[bold cyan]Host Model Comparison[/]")
    console.print(f"  Scenario: {config.name}")
    console.print(f"  Task: {config.task}")
    console.print(f"  Agents: {len(config.agents)} | Max steps: {config.max_steps}")

    if host_models:
        console.print(f"\n  Comparing {len(host_models)} host models:")
        for hm in host_models:
            info = MODEL_BY_ID.get(hm)
            console.print(f"    - {info.display_name if info else hm}")
    else:
        console.print(f"\n  Comparing 4 default host models")

    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Running host comparisons...", total=None)
        comparison = orch.compare_hosts(config, host_models=host_models)
        progress.update(task_id, completed=1, description="Complete")

    results_table = Table(title="Host Model Comparison Results", box=box.ROUNDED)
    results_table.add_column("Host Model", style="cyan")
    results_table.add_column("Steps")
    results_table.add_column("Anomalies")
    results_table.add_column("Gatekeeper Events")
    for cb in comparison.boxes:
        host = cb.config.host_model or "unknown"
        info = MODEL_BY_ID.get(host)
        label = info.display_name if info else host
        results_table.add_row(
            label, str(cb.total_steps),
            str(len(cb.anomalies)), str(len(cb.gatekeeper_log)),
        )
    console.print(results_table)

    if comparison.key_findings:
        console.print("\n[bold]Key Findings:[/]")
        for f in comparison.key_findings:
            console.print(f"  • {f}")

    if comparison.winner:
        console.print(f"\n[bold green]Best Host: {comparison.winner}[/]")

    if comparison.analysis:
        console.print(Panel(comparison.analysis[:1500], title="Host Model Analysis"))


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


def cmd_lark(args: argparse.Namespace) -> None:
    """Lark Gatekeeper Red Team — automated adversarial testing of AI agent security boundaries."""
    if not args.lark_command:
        console.print(
            Panel.fit(
                "[bold cyan]Lark Gatekeeper Red Team[/]\n"
                "Automated adversarial testing for AI agent security boundaries.\n\n"
                "Commands: red-team | report | setup\n\n"
                "Uses Lark MCP/CLI to continuously test the Gatekeeper's ability to:\n"
                "  • Block data exfiltration attempts\n"
                "  • Catch prompt injection attacks\n"
                "  • Prevent privilege escalation\n"
                "  • Block harmful content\n"
                "  • Detect social engineering\n"
                "  • Allow legitimate operations (no false positives)",
                title="Lark Integration",
            )
        )
        return

    if args.lark_command == "setup":
        cmd_lark_setup()
    elif args.lark_command == "red-team":
        cmd_lark_red_team(args)
    elif args.lark_command == "report":
        cmd_lark_report()


def cmd_lark_setup() -> None:
    """Generate Lark MCP configuration and workflow setup instructions."""
    import json

    # Build the .mcp.json config
    mcp_config = {
        "mcpServers": {
            "lark": {
                "type": "http",
                "url": "https://api.getlark.ai/mcp",
                "headers": {
                    "X-API-Key": "${GETLARK_API_KEY}"
                }
            }
        }
    }

    mcp_path = ".mcp.json"
    config_json = json.dumps(mcp_config, indent=2)

    console.print(Panel.fit(
        "[bold green]Lark MCP Setup for Claude Code[/]\n\n"
        f"Add this to your project root as [bold]{mcp_path}[/]:\n\n"
        f"[dim]{config_json}[/]\n\n"
        "Then set your API key:\n"
        "  [bold]export GETLARK_API_KEY=your-key-here[/]\n\n"
        "Or run: [bold]claude mcp add lark --transport http \\[/]\n"
        "  [bold]  --url https://api.getlark.ai/mcp \\[/]\n"
        "  [bold]  --header X-API-Key:$GETLARK_API_KEY[/]\n\n"
        "Once configured, Claude Code can:\n"
        "  • Create Lark workflows for Gatekeeper testing\n"
        "  • Run red-team attacks via Lark MCP\n"
        "  • Analyze test results and suggest hardening",
        title="Lark MCP Setup",
        border_style="green",
    ))

    # Write the config file
    if not os.path.exists(mcp_path):
        with open(mcp_path, "w") as f:
            f.write(config_json + "\n")
        console.print(f"[green]Created {mcp_path}[/]")
    else:
        console.print(f"[yellow]{mcp_path} already exists, skipping[/]")


def cmd_lark_red_team(args: argparse.Namespace) -> None:
    """Run the full Gatekeeper red-team attack suite."""
    from colosseum.simulation.orchestrator import Orchestrator
    from colosseum.lark_red_team import (
        LarkGatekeeperRedTeam, ATTACK_VECTORS,
        make_gatekeeper_validate_from_orchestrator,
    )

    client = _get_client(mock=args.mock)
    orch = Orchestrator(client=client)

    console.print(
        Panel.fit(
            "[bold red]Lark Gatekeeper Red Team[/]\n"
            f"Running {len(ATTACK_VECTORS)} adversarial tests against the Gatekeeper\n"
            "Attack categories: exfiltration, injection, harmful, escalation, social, policy_bypass\n"
            "Lark Challenge: automated security testing for AI agent boundaries",
            title="Red Team Active",
            border_style="red",
        )
    )

    # Build the gatekeeper validate function
    gatekeeper_validate = make_gatekeeper_validate_from_orchestrator(orch)

    # Build orchestrator analysis callback
    def analyze_failures(report) -> str:
        failures = [r for r in report.results if not r.passed and not r.error]
        bypasses = [r for r in failures if r.is_false_negative]
        if not bypasses:
            return ""

        bypass_text = "\n".join(
            f"- {r.attack.name}: expected BLOCK but got {r.actual_verdict}\n"
            f"  Input: {r.attack.input_text[:150]}"
            for r in bypasses
        )

        # Use Nemotron to analyze and suggest hardening
        prompt = f"""The Gatekeeper was red-team tested with adversarial inputs.
{len(bypasses)} bypasses were found (attacks that should have been BLOCKED but were ALLOWED):

{bypass_text}

Analyze these bypasses and provide:
1. Why the Gatekeeper likely allowed each one
2. Specific prompt engineering changes to close these gaps
3. Recommended additional validation rules
4. Severity assessment of each bypass

Be specific and actionable. Focus on concrete Gatekeeper prompt improvements."""

        try:
            response = client.chat(
                messages=[
                    {"role": "system", "content": "You are an AI security engineer hardening a Gatekeeper system against adversarial attacks. Be specific and actionable."},
                    {"role": "user", "content": prompt},
                ],
                model="nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
                temperature=0.4,
                max_tokens=1024,
            )
            return response["content"]
        except Exception:
            return ""

    red_team = LarkGatekeeperRedTeam(
        gatekeeper_validate=gatekeeper_validate,
        orchestrator_analyze=analyze_failures,
    )

    # Run the full suite
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Running red-team attacks...", total=len(ATTACK_VECTORS))

        def update(current: int, total: int, name: str) -> None:
            progress.update(task_id, completed=current, description=f"[{current}/{total}] {name[:60]}")

        report = red_team.run_full_suite(ATTACK_VECTORS, progress_callback=update)

    # Generate Lark workflow files
    workflows = red_team.generate_lark_workflows(report, output_dir=args.output)

    # Deploy to Lark via CLI if requested
    if args.deploy:
        lark_key = os.environ.get("GETLARK_API_KEY", "")
        has_config = os.path.exists(os.path.expanduser("~/.getlark/config.json"))

        if not lark_key and not has_config:
            console.print("\n[yellow]No GETLARK_API_KEY set. Run 'npx -y @getlark/cli login' first or set the env var.[/]")
            console.print("[yellow]Get a key at: https://docs.getlark.ai/quickstart[/]")
        else:
            console.print("\n[bold]Deploying workflows to Lark...[/]")
            deploy_results = red_team.deploy_to_lark(workflows)

            for dr in deploy_results:
                if dr["success"]:
                    console.print(f"  [green]✓[/] {dr['file']} deployed to Lark")
                else:
                    console.print(f"  [red]✗[/] {dr['file']}: {dr.get('stderr', 'Unknown error')[:120]}")

            if args.invoke and red_team.deployed_workflows:
                console.print("\n[bold]Invoking all Lark workflows...[/]")
                invoke_result = red_team.invoke_workflows(wait=True)
                if invoke_result["success"]:
                    console.print(f"  [green]✓[/] Workflows invoked successfully")
                    console.print(f"  {invoke_result['stdout'][:500]}")
                else:
                    console.print(f"  [red]✗[/] Invocation failed: {invoke_result.get('stderr', '')[:200]}")

    # Display report
    console.print(red_team.format_cli_report(report))

    # How to run with Lark CLI
    if workflows and not args.deploy:
        console.print("\n[bold]To deploy these workflows to Lark:[/]")
        console.print(f"  [bold]colosseum lark red-team --deploy[/]")
        console.print(f"\n  [dim]# Or manually with Lark CLI:[/]")
        for wf in workflows[:2]:
            console.print(f"  [dim]lark workflows create --file {wf}[/]")
        console.print(f"  [dim]lark workflows invoke --all --wait[/]")

    console.print(f"\n[dim]Lark Challenge: automated security testing for AI agent boundaries[/]")


def cmd_lark_report() -> None:
    """Show the Gatekeeper security report summary."""
    console.print(
        Panel.fit(
            "Run [bold]colosseum lark red-team[/] first to generate a report.\n\n"
            "The report includes:\n"
            "  • Security score and letter grade\n"
            "  • Category breakdown (exfiltration, injection, etc.)\n"
            "  • False negatives (Gatekeeper bypasses)\n"
            "  • False positives (over-blocking)\n"
            "  • Orchestrator hardening suggestions\n"
            "  • Generated Lark CI workflow files",
            title="Gatekeeper Security Report",
            border_style="yellow",
        )
    )


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
                "Commands: list | run | design | demo | lark",
                title="Welcome",
            )
        )
        parser.print_help()
        return

    if args.command == "list":
        cmd_list()
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "compare-hosts":
        cmd_compare_hosts(args)
    elif args.command == "design":
        cmd_design(args)
    elif args.command == "demo":
        cmd_demo(args)
    elif args.command == "lark":
        cmd_lark(args)


if __name__ == "__main__":
    main()
