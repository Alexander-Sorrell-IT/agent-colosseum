# Agent Colosseum — Architecture (DO NOT DRIFT FROM THIS)

## Core Architecture

```
User → Boundary Gatekeeper → HOST MODEL (Nemotron Super-120B)
                                    │
                           Simulation Box
                                    │
                    Box Gatekeeper validates agent actions
                                    │
              ┌─────────┬─────────┬─────────┬─────────┐
           DeepSeek   Llama     Qwen     Gemma    GPT-OSS
           (real API) (real API)(real API)(real API)(real API)
```

## What Each Part Does

### Host Model (Orchestrator)
- Nemotron Super-120B
- Designs the experiment, creates the simulation box
- Each step: receives full simulation state, decides what happens next
- Manages turn order, coherence, conflict resolution
- Analyzes results after simulation ends
- MODEL TOWN COMPARISON: swap the host model (Nemotron vs DeepSeek vs Llama)
  to compare which model hosts the best simulation

### Agents
- Backed by REAL Crusoe model API calls
- Each agent routes to its configured model (DeepSeek, Llama, Qwen, etc.)
- Agent models can differ from the host model
- The host model observes and manages them, but they produce authentic output

### Gatekeeper (Dual-Layer)
- BOUNDARY: Between user and host model — validates input/output
- BOX: Inside simulation — validates agent actions before broadcast
- Dual-agent consensus: defender + adversary both must agree to ALLOW
- 100% detection rate on Nemotron Super-120B

### Chaos Injection (TrueFoundry)
- Random 503 errors, brownouts, agent kills at configurable rate
- Tests resilience: does the system recover gracefully?

### Lark Red Team
- 24 automated attack vectors testing gatekeeper security
- Lark CLI/MCP for CI workflow deployment
- 4 live workflows on Lark cloud

## What Python Does
- Stateless dispatch layer between Crusoe API calls
- The host model gets the full state via prompt, returns structured response
- Python parses the response, routes agent calls, applies gatekeeper validation
- Python keeps the message history and broadcasts actions

## Key Invariant
- Agents ARE real API calls to their respective models
- The host model MANAGES the simulation, not a blind for-loop
- No model roleplays another model unless explicitly configured to
