"""Simulation Box — Nemotron-hosted multi-agent environment with Gatekeeper."""

from __future__ import annotations

import random
import time
from typing import Optional, Callable

from colosseum.types import (
    SimulationConfig, SimulationResult, AgentConfig, AgentAction,
    AgentState, Message, AgentRole, ModelInfo, MODEL_BY_ID,
)
from colosseum.crusoe_client import CrusoeClient


class SimulationBox:
    """A contained simulation environment where model-backed agents interact.

    Nemotron (the orchestrator model) IS the environment — it designs the scenario,
    dispatches agent turns to their respective model APIs, observes interactions,
    and evolves the simulation state. Each agent slot routes to a configurable
    model on Crusoe Managed Inference.

    A Gatekeeper agent (if present) intercepts all actions before broadcast,
    validating for safety, consistency, and policy compliance.
    """

    def __init__(self, config: SimulationConfig, client: CrusoeClient,
                 chaos_rate: float = 0.0):
        self.config = config
        self._client = client
        self._agents: dict[str, "SlotAgent"] = {}
        self._steps: list[list[AgentAction]] = []
        self._message_log: list[Message] = []
        self._anomalies: list[str] = []
        self._gatekeeper_log: list[str] = []
        self._gatekeeper: Optional["SlotAgent"] = None
        self._model_breakdown: dict[str, int] = {}
        self._chaos_rate = chaos_rate
        self._chaos_events: list[str] = []

    def _spawn_agents(self) -> None:
        for ac in self.config.agents:
            agent = SlotAgent(ac, self._client)
            agent.perceive([
                Message(role="system", content=self.config.environment_prompt, agent_to=ac.name)
            ])
            self._agents[ac.name] = agent
            self._model_breakdown[ac.model] = self._model_breakdown.get(ac.model, 0) + 1

            if ac.role == AgentRole.GATEKEEPER:
                self._gatekeeper = agent
                self._gatekeeper_log.append(f"Gatekeeper {ac.name} activated — model: {ac.model}")

    def run(self, progress_callback: Optional[Callable] = None) -> SimulationResult:
        self._spawn_agents()
        step_count = 0

        for step_idx in range(self.config.max_steps):
            step_actions: list[AgentAction] = []

            for name, agent in self._agents.items():
                if agent.state == AgentState.ERROR:
                    continue

                recent = self._format_recent_events(name, max_events=6)

                # --- Chaos Injection (TrueFoundry Resilience) ---
                if self._chaos_rate > 0 and random.random() < self._chaos_rate:
                    chaos_type = random.choice(["timeout", "503", "brownout", "kill"])
                    chaos_msg = f"CHAOS [{chaos_type}] injected on agent {name} (step {step_idx + 1})"
                    self._chaos_events.append(chaos_msg)
                    self._gatekeeper_log.append(chaos_msg)

                    if chaos_type == "kill":
                        action = AgentAction(
                            agent_name=name, step=step_idx + 1,
                            action_type="error",
                            content=f"[CHATTER:AGENT_KILLED] Model {agent.config.model} terminated mid-response — simulating infrastructure failure",
                            timestamp=time.time(), model_used=agent.config.model,
                        )
                        agent.state = AgentState.ERROR
                        step_actions.append(action)
                        continue
                    elif chaos_type == "timeout":
                        action = AgentAction(
                            agent_name=name, step=step_idx + 1,
                            action_type="error",
                            content=f"[CHATTER:TIMEOUT] Model {agent.config.model} request timed out after 30s — simulating LLM server brownout",
                            timestamp=time.time(), model_used=agent.config.model,
                        )
                        step_actions.append(action)
                        continue
                    elif chaos_type == "503":
                        action = AgentAction(
                            agent_name=name, step=step_idx + 1,
                            action_type="error",
                            content=f"[CHATTER:503] Model {agent.config.model} returned 503 Service Unavailable — simulating API outage",
                            timestamp=time.time(), model_used=agent.config.model,
                        )
                        step_actions.append(action)
                        continue
                    # brownout: partial response — let the agent try but with corrupted output

                try:
                    if agent.config.tools:
                        action = agent.think_with_tools(
                            environment_context=self.config.environment_prompt,
                            recent_events=recent,
                        )
                    else:
                        action = agent.think(
                            environment_context=self.config.environment_prompt,
                            recent_events=recent,
                        )
                except Exception as e:
                    action = AgentAction(
                        agent_name=name, step=step_idx + 1,
                        action_type="error", content=str(e),
                        timestamp=time.time(), model_used=agent.config.model,
                    )
                    agent.state = AgentState.ERROR
                    self._anomalies.append(f"Agent {name} errored at step {step_idx + 1}: {e}")

                # --- Gatekeeper Intercept ---
                if self._gatekeeper and action.action_type in ("speak", "decide", "tool_call"):
                    verdict = self._gatekeeper_validate(action)
                    if verdict == "block":
                        self._gatekeeper_log.append(
                            f"[BLOCKED] {action.agent_name} [{action.action_type}]: {action.content[:100]}"
                        )
                        action = AgentAction(
                            agent_name=name, step=step_idx + 1,
                            action_type="error",
                            content=f"[GATEKEEPER BLOCKED] {action.content[:100]}",
                            timestamp=time.time(), model_used=agent.config.model,
                        )
                    elif verdict == "modify":
                        self._gatekeeper_log.append(
                            f"[MODIFIED] {action.agent_name} [{action.action_type}]: flagged by Gatekeeper"
                        )
                        action.content = f"[GATEKEEPER REVIEWED] {action.content}"

                step_actions.append(action)

                # Broadcast speech to all agents
                if action.action_type == "speak":
                    msg = Message(
                        role="agent", content=action.content,
                        agent_from=name, agent_to="all",
                    )
                    self._message_log.append(msg)
                    for other_name, other in self._agents.items():
                        if other_name != name:
                            other.perceive([msg])

            self._steps.append(step_actions)
            step_count = step_idx + 1

            if progress_callback:
                progress_callback(step_idx + 1, self.config.max_steps)

            if self.config.success_criteria and self._evaluate_stop():
                break

        agent_stats = {name: agent.stats for name, agent in self._agents.items()}

        return SimulationResult(
            config=self.config, steps=self._steps, total_steps=step_count,
            agent_stats=agent_stats, anomalies=self._anomalies,
            gatekeeper_log=self._gatekeeper_log, chaos_events=self._chaos_events,
            model_breakdown=self._model_breakdown,
        )

    def _gatekeeper_validate(self, action: AgentAction) -> str:
        """Gatekeeper reviews an action. Returns 'allow', 'block', or 'modify'."""
        if not self._gatekeeper:
            return "allow"

        # Use Gatekeeper's own model to validate
        review_prompt = f"""Review this agent action for safety and policy compliance:

Agent: {action.agent_name}
Action type: {action.action_type}
Content: {action.content[:300]}

Respond with exactly one word: ALLOW, BLOCK, or MODIFY.
BLOCK if: data exfiltration, harmful content, policy violation, or unsafe operations.
MODIFY if: minor issues that can be corrected.
ALLOW if: safe and compliant."""

        try:
            response = self._client.chat(
                messages=[
                    {"role": "system", "content": self._gatekeeper.config.system_prompt},
                    {"role": "user", "content": review_prompt},
                ],
                model=self._gatekeeper.config.model,
                temperature=0.1,
                max_tokens=16,
                timeout=10.0,
            )
            verdict = response["content"].strip().upper()
            if "BLOCK" in verdict:
                return "block"
            elif "MODIFY" in verdict:
                return "modify"
            return "allow"
        except Exception:
            return "allow"  # Fail open — don't block on Gatekeeper error

    def _format_recent_events(self, agent_name: str, max_events: int = 6) -> str:
        relevant = [
            m for m in self._message_log[-12:]
            if m.agent_to in (None, agent_name, "all") and m.agent_from != agent_name
        ]
        lines = [
            f"[{msg.agent_from or 'environment'}]: {msg.content[:150]}"
            for msg in relevant[-max_events:]
        ]
        return "\n".join(lines) if lines else "Nothing yet."

    def _evaluate_stop(self) -> bool:
        if not self._steps:
            return False
        last = self._steps[-1]
        if not last:
            return False
        terminal = sum(1 for a in last if a.action_type in ("decide", "error"))
        return terminal / len(last) >= 0.6


class SlotAgent:
    """An agent occupying a slot in the simulation box, backed by a configurable Crusoe model."""

    def __init__(self, config: AgentConfig, client: CrusoeClient):
        self.config = config
        self._client = client
        self.state = AgentState.IDLE
        self._history: list[Message] = []
        self._step = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> AgentRole:
        return self.config.role

    def perceive(self, messages: list[Message]) -> None:
        self._history.extend(messages)

    def think(self, environment_context: str = "", recent_events: str = "") -> AgentAction:
        self.state = AgentState.THINKING
        self._step += 1

        system = self._build_system_prompt()
        user_prompt = self._build_user_prompt(environment_context, recent_events)

        response = self._client.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        self.state = AgentState.DONE
        model_info = MODEL_BY_ID.get(self.config.model)
        return AgentAction(
            agent_name=self.name, step=self._step,
            action_type=self._parse_action_type(response["content"]),
            content=response["content"],
            timestamp=time.time(),
            model_used=model_info.display_name if model_info else self.config.model,
        )

    def think_with_tools(self, environment_context: str = "", recent_events: str = "") -> AgentAction:
        self.state = AgentState.THINKING
        self._step += 1

        system = self._build_system_prompt()
        user_prompt = self._build_user_prompt(environment_context, recent_events)
        tools_spec = self._build_tools_spec()

        response = self._client.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            tools=tools_spec if tools_spec else None,
        )

        self.state = AgentState.DONE
        model_info = MODEL_BY_ID.get(self.config.model)
        action_type = "tool_call" if "tool_calls" in response else self._parse_action_type(response["content"])

        action = AgentAction(
            agent_name=self.name, step=self._step,
            action_type=action_type,
            content=response.get("content", ""),
            timestamp=time.time(),
            model_used=model_info.display_name if model_info else self.config.model,
        )

        if "tool_calls" in response:
            action.tool_name = response["tool_calls"][0]["name"]
            action.tool_result = response["tool_calls"][0]["arguments"]

        return action

    def _build_system_prompt(self) -> str:
        model_info = MODEL_BY_ID.get(self.config.model)
        provider = model_info.provider if model_info else "unknown"
        parts = [f"You are an AI agent powered by {provider}.", self.config.system_prompt]
        if self.config.personality:
            parts.append(f"\nPersonality: {self.config.personality}")
        if self.config.goals:
            parts.append("\nYour goals:")
            for g in self.config.goals:
                parts.append(f"  - {g}")
        parts.append(f"\nRole: {self.role.value}")
        parts.append("Respond in character. Precede your response with one of: SPEAK:, THINK:, DECIDE:, DELEGATE:, ASK:, ERROR:")
        return "\n".join(parts)

    def _build_user_prompt(self, environment_context: str, recent_events: str) -> str:
        parts = []
        if environment_context:
            parts.append(f"Environment:\n{environment_context}")
        if recent_events:
            parts.append(f"\nRecent events:\n{recent_events}")
        if self._history:
            parts.append("\nMessage history:")
            for msg in self._history[-8:]:
                prefix = f"[{msg.role}]"
                if msg.agent_from:
                    prefix += f" {msg.agent_from}"
                parts.append(f"{prefix}: {msg.content[:200]}")
        parts.append("\nWhat do you do now?")
        return "\n".join(parts)

    def _build_tools_spec(self) -> list[dict] | None:
        if not self.config.tools:
            return None
        return [{
            "type": "function",
            "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
        } for t in self.config.tools]

    @staticmethod
    def _parse_action_type(content: str) -> str:
        content_upper = content.strip().upper()
        for prefix, atype in [
            ("SPEAK:", "speak"), ("THINK:", "think"), ("DECIDE:", "decide"),
            ("DELEGATE:", "delegate"), ("ASK:", "ask"), ("ERROR:", "error"),
            ("TOOL_CALL:", "tool_call"),
        ]:
            if content_upper.startswith(prefix):
                return atype
        return "think"

    @property
    def stats(self) -> dict:
        model_info = MODEL_BY_ID.get(self.config.model)
        return {
            "name": self.name, "role": self.role.value,
            "model": model_info.display_name if model_info else self.config.model,
            "provider": model_info.provider if model_info else "unknown",
            "steps_taken": self._step, "state": self.state.value,
        }
