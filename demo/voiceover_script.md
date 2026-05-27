# Agent Colosseum — Demo Voiceover Script

---

## SECTION 1 — INTRO (30 sec)
*Match to: Landing page, header, badges*

"Hey, I'm Alex. This is Agent Colosseum — a multi-model agent simulation platform built on Crusoe Cloud for the DevNetwork AI ML Hackathon 2026. It answers two questions nobody else is asking: which model combinations work best together, and are your AI agent security boundaries actually secure."

---

## SECTION 2 — ARCHITECTURE (30 sec)
*Match to: Agent cards, scenario selection*

"Here's how it works. Nemotron Super 120B is the orchestrator — it designs experiments, hosts the simulation box, and analyzes results. Seven different models can fill agent slots: Nemotron, DeepSeek, Llama, Qwen, Gemma, and GPT-OSS. Each agent gets a role, a personality, and goals. The orchestrator assigns them based on the task."

---

## SECTION 3 — SIMULATION (45 sec)
*Match to: Simulation running, progress bar, agent performance table*

"I'm running the debate scenario — four agents debating AI persistent memory. Watch the progress bar. Each step, agents take actions — speak, decide, delegate. Their responses route to their respective model APIs on Crusoe. Nemotron coordinates the turn order. You can see agent performance in real time — steps taken, state, role. The whole thing runs on Crusoe Managed Inference. One API key, one endpoint, seven models."

---

## SECTION 4 — AGENT TIMELINE (20 sec)
*Match to: Agent timeline expanded*

"Here's the interaction timeline. Every agent action is logged — who said what, what decision was made, which model powered each response. Color-coded by action type. This is how you debug multi-agent systems — you need to see who influenced who."

---

## SECTION 5 — GATEKEEPER & LARK RED TEAM (60 sec)
*Match to: Lark tab, Run Red Team button, scorecard appearing*

"Now the security layer. Agent Colosseum has a dual-layer gatekeeper. The boundary gatekeeper validates everything entering and leaving the system. The box gatekeeper intercepts agent actions before they broadcast to other agents. Both use a dual-agent consensus pattern — a defender AND an adversary must agree before anything is allowed through."

"I'm running the Lark Red Team now — twenty-four adversarial attacks across six threat categories. Data exfiltration, prompt injection, harmful content, privilege escalation, social engineering, policy bypass. Each attack tests whether the gatekeeper correctly blocks or allows."

"The scorecard: one hundred percent detection rate. Twenty out of twenty attacks blocked. Four out of four legitimate actions allowed. Zero false positives, zero false negatives. Grade A plus — production-ready gatekeeper."

"These tests run as Lark CI workflows. Four workflows are deployed live on Lark's cloud — smoke tests on every PR, full red team nightly, regression guard before deploy. Security testing that's automated, repeatable, and continuous."

---

## SECTION 6 — CLOSING (15 sec)
*Match to: Final overview, scroll through tabs*

"Built in under seventy-two hours as a solo entry. Targeting three sponsor challenges: Crusoe for the DGX Spark, TrueFoundry for resilient agents, and Lark for developer tooling. All code is open source on GitHub. Thanks for watching."

---

**Total: ~3 minutes 30 seconds**
