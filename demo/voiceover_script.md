# Agent Colosseum — Trailer Voiceover Script

**Target length:** ~85 seconds of speech (matches the 95s trailer, with ~4s title silence at the start and ~5s end-card silence at the end)
**Word count:** ~210
**Tone:** an engineer telling someone how the thing came together — flowing, conversational, contractions throughout. Not a list, not an announcer.

---

## The script — read it as one continuous monologue

> When I got the Crusoe API key, I noticed the model list. Seven models, one endpoint. Most submissions here wrap one model in a chat box. I kept thinking — what if you used all of them?
>
> So Nemotron Super isn't answering questions in this demo. It runs the simulation — picking who acts, when, and what they do.
>
> Every model gets a face I generated with Perfect Corp's text-to-image API. When I click Gemma here and ask a question, the reply is a real Crusoe call routed to that exact model.
>
> The Beauty tab is the other side of Perfect Corp — a real skin-analysis API call against a face image. Ten metric scores in about eight seconds, with the ML overlays straight from their pipeline. The consumer experience their brief asks for, running for real.
>
> The Lark tab runs twenty-four adversarial attacks against the dual-agent gatekeeper. Twenty blocked. Four legitimate ones allowed through. Zero false positives.
>
> For TrueFoundry's resilience challenge, every Crusoe call retries on transient errors, the gatekeeper fails closed when the model can't be reached, and there's a chaos scenario that kills agents mid-run and watches the team adapt.
>
> Solo entry. Four sponsors. Everything you just saw, running live.

---

## What's on screen as you say each part (reference, don't read aloud)

| When you're saying | The video is showing |
|---|---|
| "When I got the Crusoe API key… seven models, one endpoint." | Sim landing — host model card, agent table |
| "Most submissions wrap one model… what if you used all of them?" | Sim landing — architecture diagram / scenario preview |
| "So Nemotron Super isn't answering questions… picking who acts." | Sim landing — agent roster + Nemotron Super avatar |
| "Every model gets a face… click Gemma here and ask…" | Talk-to-the-Catalog gallery → click Gemma → type |
| "…the reply is a real Crusoe call routed to that exact model." | Gemma reply appears on screen |
| "The Beauty tab is the other side of Perfect Corp…" | Beauty tab opens — multi-agent table visible |
| "Ten metric scores in about eight seconds…" | Skin analysis runs, 10 scores appear |
| "…ML overlays straight from their pipeline." | Beauty overlays close-up |
| "The Lark tab runs twenty-four adversarial attacks…" | Lark Red Team tab visible |
| "Twenty blocked. Four legitimate allowed. Zero false positives." | (still on Lark, hold the beat) |
| "For TrueFoundry's resilience challenge… team adapt." | Closing sim view |
| "Solo entry. Four sponsors. Everything you just saw, running live." | End card |

---

## Recording tips

- **Read it as one piece.** The paragraph breaks above are for your eyes, not your voice — let one sentence lead into the next.
- **Don't chase exact timestamps.** Talking pace ≈ 150 words per minute lands you near the visual it's describing; if you drift a second or two, the merge nudges it.
- **Contractions matter.** "Isn't / I'm / you're / that's" — they're already in the script. Don't switch back to formal.
- **The closing three short sentences are a beat, not a list.** Slight pause between them, then ride out into the end card.
- **Mic ~30 cm. mp3 / m4a / wav all merge fine.**

## After recording

1. Save the audio file anywhere (e.g. `~/Downloads/voiceover.m4a`).
2. Give the path to the assistant. It runs:
   ```
   ffmpeg -i demo/videos/agent_colosseum_trailer.mp4 -i <audio> \
          -map 0:v -map 1:a -c:v copy -c:a aac -shortest \
          demo/videos/agent_colosseum_trailer_voiced.mp4
   ```
3. Result lands at `demo/videos/agent_colosseum_trailer_voiced.mp4`, ready for Devpost upload.
