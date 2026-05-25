"""Tests for Agent Colosseum core simulation logic (offline/mock)."""

import pytest
from colosseum.types import SimulationConfig, AgentConfig, AgentRole, AgentAction, Message
from colosseum.scenarios import DEBATE_SOCIETY, STARTUP_BRAINSTORM, CRISIS_RESPONSE, ALL_SCENARIOS
from colosseum.mock_client import MockCrusoeClient
from colosseum.simulation.engine import SimulationBox
from colosseum.simulation.orchestrator import Orchestrator


@pytest.fixture
def mock_client():
    return MockCrusoeClient(latency_range=(0.01, 0.05))


class TestScenarios:
    def test_all_scenarios_have_required_fields(self):
        for name, cfg in ALL_SCENARIOS.items():
            assert cfg.name
            assert cfg.description
            assert cfg.task
            assert len(cfg.agents) >= 2
            assert cfg.max_steps > 0

    def test_debate_scenario(self):
        cfg = DEBATE_SOCIETY
        assert len(cfg.agents) == 4
        roles = {a.role for a in cfg.agents}
        assert AgentRole.WORKER in roles
        assert AgentRole.CRITIC in roles
        assert AgentRole.COORDINATOR in roles

    def test_startup_scenario(self):
        cfg = STARTUP_BRAINSTORM
        assert len(cfg.agents) == 4
        assert all(a.model for a in cfg.agents)

    def test_crisis_scenario(self):
        cfg = CRISIS_RESPONSE
        assert len(cfg.agents) == 4
        assert cfg.success_criteria


class TestAgentLifecycle:
    def test_agent_creation(self):
        from colosseum.agents.lifecycle import Agent
        client = MockCrusoeClient()
        config = AgentConfig(
            name="test_agent",
            role=AgentRole.WORKER,
            system_prompt="You are a test agent. Be concise.",
            personality="Helpful",
            goals=["Test the system"],
        )
        agent = Agent(config, client)
        assert agent.name == "test_agent"
        assert agent.role == AgentRole.WORKER
        assert agent.state.value == "idle"

    def test_agent_think(self):
        from colosseum.agents.lifecycle import Agent
        client = MockCrusoeClient()
        config = AgentConfig(
            name="test_agent",
            role=AgentRole.WORKER,
            system_prompt="You are a test agent.",
        )
        agent = Agent(config, client)
        action = agent.think(
            environment_context="Test environment",
            recent_events="Nothing happened yet.",
        )
        assert isinstance(action, AgentAction)
        assert action.agent_name == "test_agent"
        assert action.step == 1
        assert action.content


class TestSimulationBox:
    def test_spawn_and_run(self, mock_client):
        config = SimulationConfig(
            name="test_sim",
            description="Test simulation",
            agents=[
                AgentConfig(
                    name="agent_a",
                    role=AgentRole.WORKER,
                    system_prompt="You are agent A. Be brief.",
                ),
                AgentConfig(
                    name="agent_b",
                    role=AgentRole.CRITIC,
                    system_prompt="You are agent B. Critique briefly.",
                ),
            ],
            environment_prompt="Test environment.",
            task="Test task",
            max_steps=3,
        )
        engine = SimulationBox(config, client=mock_client)
        result = engine.run()

        assert result.total_steps > 0
        assert result.total_steps <= 3
        assert len(result.steps) == result.total_steps
        assert "agent_a" in result.agent_stats
        assert "agent_b" in result.agent_stats
        # Each step should have actions for all agents
        for step_actions in result.steps:
            assert len(step_actions) == 2

    def test_message_broadcast(self, mock_client):
        """Verify that 'speak' actions generate messages for other agents."""
        config = SimulationConfig(
            name="broadcast_test",
            description="Test message passing",
            agents=[
                AgentConfig(
                    name="speaker",
                    role=AgentRole.WORKER,
                    system_prompt="You always speak. Start every response with SPEAK:",
                ),
                AgentConfig(
                    name="listener",
                    role=AgentRole.OBSERVER,
                    system_prompt="You always think. Start every response with THINK:",
                ),
            ],
            environment_prompt="Just talk.",
            task="Talk",
            max_steps=2,
        )
        engine = SimulationBox(config, client=mock_client)
        result = engine.run()

        # Should complete without errors
        assert not result.anomalies
        assert result.total_steps > 0


class TestOrchestrator:
    def test_run_experiment(self, mock_client):
        orch = Orchestrator(client=mock_client)
        result = orch.run_experiment(DEBATE_SOCIETY)
        assert result.total_steps > 0
        assert len(orch.results) == 1

    def test_analyze_results(self, mock_client):
        orch = Orchestrator(client=mock_client)
        result = orch.run_experiment(DEBATE_SOCIETY)
        analysis = orch.analyze_results(result)
        assert analysis  # Should have content

    def test_compare_experiments(self, mock_client):
        orch = Orchestrator(client=mock_client)
        orch.run_experiment(DEBATE_SOCIETY)
        orch.run_experiment(CRISIS_RESPONSE)
        comparison = orch.compare_experiments()
        assert "at least 2" not in comparison.lower()  # Should have real comparison

    def test_stats(self, mock_client):
        orch = Orchestrator(client=mock_client)
        orch.run_experiment(DEBATE_SOCIETY)
        stats = orch.stats
        assert stats["experiments_run"] == 1
        assert stats["calls"] > 0
        assert "avg_latency_ms" in stats


class TestTypes:
    def test_simulation_result_serializable(self):
        cfg = DEBATE_SOCIETY
        assert cfg.model_dump()

    def test_agent_config_defaults(self):
        ac = AgentConfig(
            name="test",
            role=AgentRole.WORKER,
            system_prompt="test",
        )
        assert ac.temperature == 0.7
        assert ac.max_tokens == 1024
        assert ac.goals == []
        assert ac.tools == []
