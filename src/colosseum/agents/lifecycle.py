"""Simulated agent lifecycle — think, speak, act, decide."""

from __future__ import annotations

import time
from typing import Optional

from colosseum.types import AgentConfig, AgentState, AgentAction, AgentRole, Message
from colosseum.crusoe_client import CrusoeClient


class Agent:
    """A simulated AI agent that thinks, acts, and communicates."""

    def __init__(self, config: AgentConfig, client: CrusoeClient):
        self.config = config
        self._client = client
        self.state = AgentState.IDLE
        self._history: list[Message] = []
        self._step = 0
        self._tools_used: list[str] = []
        self._messages_sent = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> AgentRole:
        return self.config.role

    def perceive(self, messages: list[Message]) -> None:
        """Receive messages from environment or other agents."""
        self._history.extend(messages)

    def think(self, environment_context: str = "", recent_events: str = "") -> AgentAction:
        """Produce a thought/action via LLM inference."""
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

        content = response["content"]
        action = self._parse_action(content)
        self.state = AgentState.DONE
        return action

    def think_with_tools(
        self,
        environment_context: str = "",
        recent_events: str = "",
    ) -> AgentAction:
        """Produce a thought/action with tool-calling capability."""
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

        if "tool_calls" in response:
            action = AgentAction(
                agent_name=self.name,
                step=self._step,
                action_type="tool_call",
                content=response.get("content", ""),
                tool_name=response["tool_calls"][0]["name"],
                tool_result=response["tool_calls"][0]["arguments"],
                timestamp=time.time(),
            )
        else:
            action = self._parse_action(response["content"])

        self.state = AgentState.DONE
        return action

    def _build_system_prompt(self) -> str:
        parts = [self.config.system_prompt]
        if self.config.personality:
            parts.append(f"\nPersonality: {self.config.personality}")
        if self.config.goals:
            parts.append("\nYour goals:")
            for g in self.config.goals:
                parts.append(f"  - {g}")
        parts.append(f"\nYour role: {self.role.value}")
        parts.append("\nRespond in character. Choose ONE action per turn: think, speak, tool_call, decide, delegate, or ask.")
        parts.append("Format your response as: [ACTION_TYPE]: <your content>")
        return "\n".join(parts)

    def _build_user_prompt(self, environment_context: str, recent_events: str) -> str:
        parts = []
        if environment_context:
            parts.append(f"Environment:\n{environment_context}")
        if recent_events:
            parts.append(f"\nRecent events:\n{recent_events}")
        if self._history:
            recent_msgs = self._history[-6:]
            parts.append("\nRecent messages:")
            for msg in recent_msgs:
                prefix = f"[{msg.role}]"
                if msg.agent_from:
                    prefix += f" {msg.agent_from}"
                parts.append(f"{prefix}: {msg.content[:200]}")
        parts.append("\nWhat do you do?")
        return "\n".join(parts)

    def _build_tools_spec(self) -> list[dict] | None:
        if not self.config.tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.config.tools
        ]

    def _parse_action(self, content: str) -> AgentAction:
        """Parse LLM output into a typed AgentAction."""
        content = content.strip()
        action_type = "think"
        cleaned = content

        prefixes = {
            "SPEAK:": "speak",
            "THINK:": "think",
            "DECIDE:": "decide",
            "DELEGATE:": "delegate",
            "ASK:": "ask",
            "TOOL_CALL:": "tool_call",
            "ERROR:": "error",
        }
        for prefix, atype in prefixes.items():
            if content.upper().startswith(prefix):
                action_type = atype
                cleaned = content[len(prefix):].strip()
                break

        return AgentAction(
            agent_name=self.name,
            step=self._step,
            action_type=action_type,  # type: ignore[arg-type]
            content=cleaned,
            timestamp=time.time(),
        )

    @property
    def stats(self) -> dict:
        return {
            "name": self.name,
            "role": self.role.value,
            "steps_taken": self._step,
            "tools_used": len(self._tools_used),
            "messages_sent": self._messages_sent,
            "state": self.state.value,
        }
