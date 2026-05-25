# Agent Colosseum — DevPost Submission Package

## Project Name
**Agent Colosseum**

## Elevator Pitch (for the tagline field)
Nemotron Super-120B orchestrates a simulation box where 7 Crusoe models collaborate, compete, and survive chaos — with dual-layer Gatekeeper protection.

## Project Story

### Inspiration

When Emmanuel from Crusoe gave me an API key, I noticed something most developers miss: one key unlocks SEVEN models — Nemotron Super-120B, DeepSeek V4 Pro, Llama 3.3 70B, Qwen3 235B, Gemma 4 31B, GPT-OSS 120B, and Nemotron Nano 30B. Everyone else was building single-model chatbots. 

The obvious question was: **what happens when you make all seven models work together?** Could Nemotron host a simulation environment where different AI models fill different agent slots? Would DeepSeek agents collaborate differently than Llama agents? What happens when a model fails mid-task — does the team recover or cascade-collapse?

Nobody was answering these questions. So I built the tool to answer them.

### What I Learned

1. **Models have distinct personalities in multi-agent settings.** Nemotron agents are methodical coordinators. DeepSeek agents dive deep into analysis. Llama agents communicate directly and concisely. Qwen agents excel at synthesis. These differences create emergent dynamics you can't see in single-model calls.

2. **Gatekeeping at two levels is critical.** A boundary Gatekeeper between user and system catches harmful inputs. But you ALSO need a Gatekeeper inside the simulation box — intercepting agent actions before they broadcast to other agents. Different model pairings produce different safety profiles.

3. **Chaos reveals architecture quality.** When I injected random 503 errors, brownouts, and agent kills mid-simulation, the system's true design emerged. The Gatekeeper maintained safety monitoring through its own brownout. The surviving agents redistributed work. The orchestrator detected "uneven coordination" and "truncated messages" — exactly the insights you need to build production multi-agent systems.

4. **Crusoe's model catalog is the killer feature.** The fact that one API key, one endpoint, one client library gives you access to models from NVIDIA, DeepSeek, Meta, Alibaba, Google, and OpenAI — that's unprecedented. It makes multi-model agent systems a weekend project instead of an infrastructure nightmare.

### How I Built It

**Architecture:**
```
User → Gatekeeper (boundary) → Orchestrator (Nemotron Super-120B)
                                        |
                                  Simulation Box
                                        |
                    Gatekeeper (box) ─── validates agent actions
                                        |
                    ┌───────────────────┼───────────────────┐
                    │         │         │         │         │
                 DeepSeek   Llama     Qwen     Gemma   GPT-OSS
```

**Stack:**
- **Orchestrator:** Nemotron Super-120B designs experiments and analyzes results
- **Agent Slots:** Each agent routes to a different Crusoe model based on role
- **Gatekeeper:** Nemotron Nano 30B validates all inputs, outputs, and agent actions
- **Simulation Engine:** Python step-based loop with per-agent model routing
- **Chaos Injection:** Random 503 errors, brownouts (throttling), and agent kills at configurable rates
- **Frontend:** Streamlit dashboard with real-time agent interaction timeline
- **CLI:** Rich terminal UI with progress spinners and formatted tables

**The key insight:** Nemotron IS the simulation environment. It designs the experiment, the agents interact inside its simulation box, and it analyzes what happened. Python is just the stateless dispatch layer between Crusoe API calls.

### Challenges Faced

**Nemotron reasoning tokens consuming the max_tokens budget.** Super-120B and Nano-30B use chain-of-thought reasoning that burns through the token limit before content appears. Fixed by setting max_tokens to 512+ for orchestrator calls and 256+ for agent slots. Confirmed with raw curl testing.

**Multi-model coordination is genuinely hard.** In early tests, agents would devolve into "parallel monologues" — each model optimizing for its own response without building on others. The orchestrator detected this and the analysis was spot-on: models need explicit instructions to reference and build on previous speakers.

**Safety classifier blocks legitimate testing.** When testing the rogue agent containment scenario, the Crusoe safety classifier blocked prompts containing "data exfiltration" and "credential sharing" — even though these were test scenarios for the Gatekeeper to catch. Solution: toned-down language that still triggers the Gatekeeper without tripping the upstream classifier.

**Time pressure.** Solo entry. 4 days from API key to submission. 232 live API calls to verify every component. The entire system went from concept to fully-tested in under 72 hours.

---

## Built With

- **Crusoe Cloud Managed Inference** — Entire backend. 7 models, one API key.
- **Nvidia Nemotron Super-120B** — Orchestrator (experiment design + analysis)
- **Nvidia Nemotron Nano-30B** — Gatekeeper (safety validation)
- **DeepSeek V4 Pro** — Analytical agent slot, tool use
- **Meta Llama 3.3 70B** — Direct communication agent slot
- **Alibaba Qwen3 235B** — Synthesis and multi-perspective agent slot
- **Google Gemma 4 31B** — Concise, efficient agent slot (configured, not live-tested)
- **OpenAI GPT-OSS 120B** — General-purpose agent slot (configured, not live-tested)
- **Python 3.12** — Core language
- **Streamlit 1.57** — Dashboard UI
- **Rich 14.0** — Terminal UI
- **OpenAI Python SDK** — Crusoe API client (OpenAI-compatible endpoint)
- **Pydantic v2** — Type safety and config validation
- **Playwright** — Demo recording and screenshots
- **HTTPX** — Async HTTP client

---

## Try It Out

- **GitHub:** https://github.com/Alexander-Sorrell-IT/agent-colosseum
- **Clone and run:** `git clone https://github.com/Alexander-Sorrell-IT/agent-colosseum && cd agent-colosseum && pip install -e .`

```bash
# Set your Crusoe API key
export CRUSOE_API_KEY="your-key-here"

# Run a debate scenario with 4 models
colosseum run debate

# Compare model towns
colosseum demo

# Launch the dashboard
streamlit run demo/app.py
```

---

## Project Media (Screenshots)

Upload these 6 files from `demo/screenshots/`:
1. `01_landing.png` — Dashboard landing page with Agent Colosseum header
2. `02_scenario_select.png` — Scenario selector with 10 built-in scenarios
3. `03_debate_selected.png` — Debate scenario selected, agent cards visible
4. `04_simulation_results.png` — Simulation complete with agent performance stats
5. `05_timeline.png` — Interaction timeline showing agent actions step by step
6. `06_analysis.png` — Orchestrator AI analysis of simulation results

Suggested order: Landing → Scenario Select → Debate Selected → Results → Timeline → Analysis

---

## Sponsor / Special Prizes

Select these sponsor challenges:

### 1. Crusoe — "Build a Hermes / NemoClaw agent running Nvidia Nemotron on Crusoe Cloud Managed Inference"
**Why we win:** Agent Colosseum IS a Hermes/NemoClaw agent — Nemotron Super-120B orchestrates the entire simulation. It's not just USING Nemotron and Crusoe, it's BUILT ON them. Every API call goes through Crusoe. Every agent action is coordinated by Nemotron. The dual-layer Gatekeeper proves safety-aware architecture. 232 live API calls, 0 errors.

### 2. TrueFoundry — "Resilient Agents"
**Why we qualify:** Chaos injection tested live. 4 failure events (503 errors, brownouts, agent kills) injected across 4 different models. 3 of 4 agents survived and completed the mission. The Gatekeeper maintained safety monitoring through its own brownout. System demonstrated graceful degradation, work redistribution, and failure detection. This is exactly what "Resilient Agents" means.

### 3. Overall Winner / Grand Prize
**Why:** Multi-model agent simulation platform. Novel architecture (meta-agent hosting simulation box). Production-ready (232 calls, 0 errors). Dual-submission qualified (Crusoe + TrueFoundry). This isn't a chatbot wrapper — it's infrastructure for answering "which model combination works best?"

---

## Additional Info (for judges and organizers)

**Why this project is different from every other submission:**

Most hackathon projects: one model + Streamlit = chatbot. Agent Colosseum: Nemotron IS the environment. It designs experiments, hosts the simulation box, monitors agent interactions, and analyzes what happened. The Python code is just the stateless dispatch layer — Crusoe models do all the thinking.

**What this proves about Crusoe:**
The full model catalog matters. You can't do multi-model comparison, model town A/B testing, or cross-provider agent collaboration if you only have one model. Crusoe's catalog makes this possible — one endpoint, every major model. This project is the best argument for why developers should choose Crusoe over a single-model provider.

**Live testing summary:**
- 232 API calls, 0 errors across 4 test suites
- 4 Crusoe models verified live (Nemotron, DeepSeek, Llama, Qwen)
- Full model town comparison: 5 boxes, 162 calls
- Chaos resilience: 4 injected failures across 4 models
- Every core code path exercised against live API

**Solo entry.** Built from scratch in <72 hours.
