**To:** eacheampong@crusoe.ai
**Subject:** Agent Colosseum — submitted. 100% A+ Gatekeeper on Nemotron Super. Quick Crusoe notes.

---

Hi Emmanuel,

Just submitted Agent Colosseum to the DevNetwork AI+ML Hackathon. Wanted to send a short heads-up since Crusoe is the entire backend.

**What I built**
A meta-agent platform where Nvidia Nemotron Super-120B orchestrates a simulation arena, and each agent slot routes to a different model in your catalog — DeepSeek V4 Pro, Llama 3.3 70B, Qwen3 235B, Gemma 4 31B, GPT-OSS 120B. Every model gets a Perfect-Corp-generated character; user picks an avatar and chats with that exact model behind a real Crusoe inference call. Solo entry, four sponsor challenges (Crusoe, Perfect Corp, Lark, TrueFoundry).

**GitHub:** https://github.com/Alexander-Sorrell-IT/agent-colosseum
**Devpost:** [paste your project URL]
**Trailer:** [paste your YouTube URL]

**Verified live yesterday (≈250 Crusoe calls, 0 user-visible failures):**
- 6 models exercised in chat completions
- Dual-agent Gatekeeper on Nemotron Super-120B — **24/24 = 100% A+** on a 24-attack adversarial red team, re-verified end-to-end
- 5 simulation scenarios with 0 anomalies (crisis, chaos, 4 model-towns)
- Live Perfect Corp Skin Analysis routing in the Beauty tab
- 5 Lark CI workflows deployed live on Lark Cloud

**Two notes from the verification sweep — flagging for the Crusoe team in case useful:**

1. `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` is listed in `/v1/models` but `POST /v1/chat/completions` returns `404 model_not_found`. Catalog/inference inconsistency on that specific Nano variant — same key works fine against Super, DeepSeek, Llama, Qwen, Gemma, GPT-OSS.

2. The Nemotron reasoning models eat the entire `max_tokens` budget with chain-of-thought before content appears. Your published sponsor curl reproduces this — HTTP 200 in 121s with empty content because the example uses `max_tokens=128`. Anything under ~1024 returns blank. Worth noting in the sample docs since it cost me hours to track down.

**Quick question on the foundry credits:** I registered at request-foundry but I'm not sure whether credits are tracked automatically against the key you provisioned or if there's a separate step. If you can point me in the right direction, I'd appreciate it.

Thanks again for the API key. It was rock solid — every "flake" I saw turned out to be either fixable client-side (retry on transient transport errors) or the two issues above.

Best,
Alexander Sorrell
DevNetwork AI+ML Hackathon 2026 (solo)
