"""Core types for the Agent Colosseum."""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    OBSERVER = "observer"
    CRITIC = "critic"
    COORDINATOR = "coordinator"
    GATEKEEPER = "gatekeeper"


class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


class Severity(str, Enum):
    CRITICAL = "critical"
    MODERATE = "moderate"
    MINOR = "minor"


# --- Model Catalog ---

class ModelInfo(BaseModel):
    """Metadata for a model available on Crusoe Managed Inference."""
    id: str
    provider: str  # e.g. "nvidia", "deepseek", "meta", "google", "qwen", "openai"
    display_name: str
    best_for: str = ""  # e.g. "orchestrator", "agent-slot", "reasoning"
    input_price_per_m: float = 0.0
    output_price_per_m: float = 0.0
    context_length: int = 131072
    supports_tools: bool = False


AVAILABLE_MODELS: list[ModelInfo] = [
    ModelInfo(id="nvidia/NVIDIA-Nemotron-3-Super-120B-A12B", provider="nvidia",
              display_name="Nemotron Super 120B", best_for="orchestrator",
              input_price_per_m=0.30, output_price_per_m=2.40, context_length=262144),
    ModelInfo(id="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", provider="nvidia",
              display_name="Nemotron Nano 30B", best_for="agent-slot",
              input_price_per_m=0.05, output_price_per_m=0.20, context_length=262144),
    ModelInfo(id="deepseek-ai/DeepSeek-V4-Pro", provider="deepseek",
              display_name="DeepSeek V4 Pro", best_for="agent-slot",
              input_price_per_m=1.74, output_price_per_m=3.48, context_length=1048576,
              supports_tools=True),
    ModelInfo(id="meta-llama/Llama-3.3-70B-Instruct", provider="meta",
              display_name="Llama 3.3 70B", best_for="agent-slot",
              input_price_per_m=0.25, output_price_per_m=0.75, context_length=131072),
    ModelInfo(id="Qwen/Qwen3-235B-A22B-Instruct-2507", provider="qwen",
              display_name="Qwen3 235B", best_for="agent-slot",
              input_price_per_m=0.22, output_price_per_m=0.80, context_length=262144),
    ModelInfo(id="google/gemma-4-31b-it", provider="google",
              display_name="Gemma 4 31B", best_for="agent-slot",
              input_price_per_m=0.14, output_price_per_m=0.40, context_length=262144),
    ModelInfo(id="openai/gpt-oss-120b", provider="openai",
              display_name="GPT-OSS 120B", best_for="agent-slot",
              input_price_per_m=0.05, output_price_per_m=0.25, context_length=131072),
    ModelInfo(id="nvidia/NVIDIA-Nemotron-3-VoiceChat", provider="nvidia",
              display_name="Nemotron VoiceChat", best_for="voice",
              input_price_per_m=0, output_price_per_m=0, context_length=131072),
]

MODEL_BY_ID: dict[str, ModelInfo] = {m.id: m for m in AVAILABLE_MODELS}
MODELS_FOR_AGENTS = [m for m in AVAILABLE_MODELS if m.best_for in ("agent-slot", "orchestrator")]
DEFAULT_ORCHESTRATOR_MODEL = "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B"
DEFAULT_AGENT_MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"


# --- Core Types ---

class Message(BaseModel):
    """A message between agents or from environment to agent."""
    role: Literal["system", "user", "assistant", "agent", "environment"]
    content: str
    agent_from: Optional[str] = None
    agent_to: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Tool(BaseModel):
    """A tool an agent can call."""
    name: str
    description: str
    parameters: dict = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for a simulated agent."""
    name: str
    role: AgentRole
    system_prompt: str
    tools: list[Tool] = Field(default_factory=list)
    model: str = DEFAULT_AGENT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1024
    personality: str = ""
    goals: list[str] = Field(default_factory=list)


class AgentAction(BaseModel):
    """An action taken by an agent during simulation."""
    agent_name: str
    step: int
    action_type: Literal["think", "speak", "tool_call", "decide", "delegate", "ask", "error"]
    content: str
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None
    target: Optional[str] = None
    timestamp: float = 0.0
    model_used: str = ""


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""
    name: str
    description: str
    agents: list[AgentConfig]
    environment_prompt: str
    max_steps: int = 50
    task: str = ""
    success_criteria: str = ""


class SimulationResult(BaseModel):
    """Results from a completed simulation."""
    config: SimulationConfig
    steps: list[list[AgentAction]]
    total_steps: int
    agent_stats: dict[str, dict] = Field(default_factory=dict)
    analysis: str = ""
    anomalies: list[str] = Field(default_factory=list)
    gatekeeper_log: list[str] = Field(default_factory=list)
    chaos_events: list[str] = Field(default_factory=list)
    model_breakdown: dict[str, int] = Field(default_factory=dict)


class BoxComparison(BaseModel):
    """Comparison of multiple simulation boxes."""
    boxes: list[SimulationResult] = Field(default_factory=list)
    models_tested: list[str] = Field(default_factory=list)
    winner: str = ""
    analysis: str = ""
    key_findings: list[str] = Field(default_factory=list)
