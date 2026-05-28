# Agent Colosseum — Devpost Submission Packet

**Paste each section directly into the corresponding Devpost form field.**
Hackathon: DevNetwork AI+ML Hackathon 2026
Deadline: 2026-05-28 12:00 PM CDT
Type: Solo entry
Repo: https://github.com/Alexander-Sorrell-IT/agent-colosseum

---

## 1. Project name

```
Agent Colosseum
```

## 2. Tagline / elevator pitch (max 200 chars on Devpost)

```
One Crusoe API key, seven LLMs working as one. Nvidia Nemotron Super-120B orchestrates a simulation arena; every model has a Perfect-Corp-generated face. Talk to any. Test any. Watch them collaborate.
```

## 3. Project description (long form — main story field)

```
## Inspiration

When I got the Crusoe API key, the first thing I noticed was the model list. Seven different models — Nvidia Nemotron Super-120B, Nemotron Nano-30B, DeepSeek V4 Pro, Meta Llama 3.3 70B, Alibaba Qwen3 235B, Google Gemma 4 31B, OpenAI GPT-OSS 120B — all behind one endpoint, one key. Most hackathon submissions pick one model and build a chat window. I wanted to know what happens when you make all of them work together.

That's Agent Colosseum: a meta-agent platform where Nemotron Super-120B doesn't just answer questions — it runs an entire simulation environment. It designs experiments, picks which agents speak, schedules turns, gatekeeps unsafe actions, and analyzes what happened afterward. Each agent slot is filled by a different Crusoe model with its own role, personality, and goals.

## What it does

**Multi-model simulation arena.** Pick a scenario — debate, crisis response, beauty consultation, chaos resilience — and Nemotron Super hosts an environment where each agent is backed by a different Crusoe model. The agents collaborate, disagree, redistribute work when one fails, and converge on an outcome. Built-in scenarios include single-provider towns (all-DeepSeek, all-Llama, all-Qwen, mixed) so you can compare collaboration styles across providers.

**Talk to the Catalog.** Every model in the catalog has a face — visual identities generated live by Perfect Corp's text-to-image API. Click a model, type a question, and the reply you see is a real Crusoe inference call to that exact endpoint. Same flow for any of the seven models.

**Perfect Corp Beauty AI.** A face image goes in. Ten metric scores come back — texture, pores, wrinkles, acne, dark circles, oiliness, moisture, radiance, age spots, redness — plus an overall skin score, an estimated skin age, and ML overlays from Perfect Corp's pipeline. All in the browser, all in about eight seconds. The consumer experience their challenge asks for, running for real.

**Lark Gatekeeper Red Team.** A dual-agent gatekeeper (defender + adversary, both on Nemotron Super) decides what's allowed to enter the simulation. To prove it works, 24 adversarial attack vectors test it continuously — data exfiltration, prompt injection, harmful content, privilege escalation, social engineering, policy bypass. Verified live the day before submission: 24/24 = 100% A+ detection. Lark CI workflows are deployed live on Lark Cloud with real wflw_ IDs — smoke tests, full red-team suite, regression guard, repo smoke test.

**Resilient agents (TrueFoundry challenge).** When the infrastructure breaks, the system breaks gracefully. CrusoeClient disables SDK retries for predictable timeouts then retries once in-wrapper for transient transport errors. The gatekeeper retries each call once, then fails closed if the retry also fails — surfacing infrastructure errors instead of silently allowing traffic through. The resilience_chaos scenario injects agent kills, brownouts, and 503 errors; the system handles them with zero anomalies. TrueFoundry AI Gateway integration code is in-repo as a drop-in OpenAI-compatible client.

## How I built it

- **Host / orchestrator:** Nvidia Nemotron Super-120B running on Crusoe Cloud Managed Inference. Designs experiments, schedules turns, validates actions, analyzes outcomes.
- **Agent slots:** Each slot routes to a different Crusoe model. Six models verified live in chat completions today.
- **Visual layer:** Perfect Corp YouCam Enterprise (YCE) — text-to-image for character avatars, AI Skin Analysis for the Beauty tab, virtual try-on stubs ready for makeup/hair/fashion.
- **Gatekeeper:** Dual-agent consensus on Nemotron Super 120B. Defender + adversary both must agree to ALLOW. Retry-once-then-fail-closed.
- **Frontend:** Streamlit dashboard with 4 tabs (Simulation, Lark Gatekeeper Red Team, Perfect Corp Beauty AI, Talk to the Catalog).
- **CLI:** Rich terminal UI — `colosseum list`, `colosseum run`, `colosseum design`, `colosseum lark red-team --deploy`, `colosseum demo`.
- **Lark CI:** 5 workflows deployed on Lark Cloud, generated automatically from red-team output.
- **TrueFoundry:** Drop-in OpenAI-compatible client wired at src/colosseum/truefoundry_gateway.py. Live auth verified; provider-account creation blocked by Developer Plan schema validation (evidence in screenshots 09–11).

## What I learned

1. **Models have distinct personalities in multi-agent settings.** Nemotron Super coordinates methodically. DeepSeek drills into analysis. Llama communicates directly. Qwen synthesizes across perspectives. These differences create emergent dynamics you can't see in single-model calls.

2. **Visual identity changes how you reason about model differences.** When the catalog goes from text labels to faces, "which model is in which slot" stops being abstract.

3. **Gatekeeper fail-open is silent and dangerous.** My first 24-attack red team scored 91.7% Grade A — but the two "false negatives" were actually infrastructure errors silently converted to ALLOW by a broad `except: return True`. Replacing it with retry-then-fail-closed surfaced the issue and the verified score became 100% A+.

4. **Nemotron reasoning tokens eat max_tokens.** Calls with max_tokens<1024 returned empty content as the chain-of-thought burned the budget. Crusoe's own published sponsor curl reproduces this: HTTP 200 in 121.9s with empty content because the example uses max_tokens=128. Bumped to 1024 across the codebase.

5. **Crusoe's catalog is the killer feature.** One key, seven models. Multi-model comparison, model-town A/B testing, cross-provider agent collaboration — none of this is possible with a single-model provider.

## Challenges I faced

- **Perfect Corp client was broken end-to-end.** The original integration sent base64 in the auth body. The real flow is presigned S3 PUT URL, path-param task IDs, `task_status` (not `status`) as the success field. Rewrote the client against the live API and verified: 134 KB clay-style hero image in 4 calls / 5.8 seconds, 4 trailer hero shots in 16 seconds, 7 model avatars in 37 seconds.
- **Crusoe transient errors.** Today, 4 transient errors across 200+ verification calls. The retry-once wrapper transparently recovered all of them.
- **TF Custom Endpoint blocked on Developer Plan.** Walked the form through all 3 steps; backend rejects `provider-account/custom-endpoint` type with `aws_account_id required`. Wire is ready; flipping a paid tier or a TF backend fix activates it.
- **Time pressure.** Solo entry, four-sponsor coverage, ~250 live API verifications across Crusoe, Perfect Corp, and Lark on the day before submission.

## What's next

- Persistent simulation history and replay
- Custom scenario builder UI
- Real-time multi-human collaboration with AI agents in the same arena
- Full TrueFoundry AI Gateway routing once the Custom Endpoint type is unblocked
- More avatar styles per model (Perfect Corp templates support 12+ styles)
```

## 4. Built With (tag list)

```
crusoe-cloud
nvidia-nemotron
perfect-corp
lark-cli
truefoundry
python
streamlit
playwright
openai-sdk
pydantic
deepseek
llama
qwen
gemma
gpt-oss
ffmpeg
```

## 5. Try It Out links

```
GitHub: https://github.com/Alexander-Sorrell-IT/agent-colosseum
```

## 6. Video URL (paste once YouTube upload finishes)

```
[YouTube URL — fill in after upload]
```

## 7. Sponsor challenges to select (check all on Devpost)

- ☑ **Crusoe** — "Build a Hermes / NemoClaw agent running Nvidia Nemotron on Crusoe Cloud Managed Inference"
- ☑ **Perfect Corp** — "Building the Next Generation of AI-Driven Consumer Experiences"
- ☑ **Lark** — "Best Use of Lark CLI and/or MCP"
- ☑ **TrueFoundry** — "Resilient Agents"
- ☑ **DevNetwork [AI + ML] Hackathon 2026 Overall Winner**

## 8. Files to upload on Devpost

| Slot | File |
|---|---|
| Thumbnail / cover image | `demo/thumbnail.png` (1200×800) |
| Demo video | YouTube URL after upload (the file is at `demo/videos/agent_colosseum_trailer_voiced.mp4`) |
| Screenshot 1 | `demo/screenshots/01_landing.png` — Simulation tab landing |
| Screenshot 2 | `demo/screenshots/02_avatar_gallery.png` — Talk to the Catalog |
| Screenshot 3 | `demo/screenshots/03_avatar_chat.png` — live Gemma chat |
| Screenshot 4 | `demo/screenshots/04_beauty_landing.png` — Beauty tab agent table |
| Screenshot 5 | `demo/screenshots/05_beauty_skin_analysis.png` — live skin scores |
| Screenshot 6 | `demo/screenshots/06_lark_red_team.png` — Lark Red Team tab |
| Screenshot 7 | `demo/screenshots/12_sim_run_timeline.png` — sim mid-run with avatars |
| Screenshot 8 | `demo/screenshots/14_beauty_overlays.png` — ML overlays close-up |
| Screenshot 9 | `demo/screenshots/11_tf_backend_error.png` — TrueFoundry integration evidence |

## 9. Devpost form sequence (recommended click order)

1. Project Name → paste from §1
2. Tagline → paste from §2
3. Long description → paste from §3
4. Built With → comma-separate or tag-by-tag from §4
5. Try It Out → §5
6. Video URL → §6 (after YouTube upload)
7. Upload thumbnail + 9 screenshots (§8)
8. Select sponsor challenges (§7)
9. Confirm team is solo (just you)
10. **Submit**

## 10. Last-mile checklist before clicking Submit

- ☐ YouTube video uploaded, URL pasted into §6
- ☐ Thumbnail uploaded
- ☐ At least 6 screenshots uploaded (Devpost minimum varies)
- ☐ All four sponsor checkboxes ticked + Overall Winner
- ☐ Tagline under 200 chars
- ☐ Submitted before 12:00 PM CDT Thursday 2026-05-28
