# Agent Colosseum — Trailer Voiceover Script

**Target length:** ~95 seconds (matches `demo/videos/agent_colosseum_trailer.mp4`)
**Word count:** ~195 (≈150 wpm with breath beats)
**Tone:** confident, conversational engineer — not announcer

Bracketed `[…]` marks are breath beats. Bracketed `[mm:ss]` cues match the trailer timeline so you can read along while it plays.

---

### [0:00 — title card]

> Agent Colosseum. Multi-model AI on Crusoe Cloud. [...]

---

### [0:04 — Sim landing, agent table appears]

> Most hackathon entries wrap a single model in a chatbot. This is different. Nemotron Super-120B isn't just answering questions — it's running an entire simulation environment. [...] It designs experiments, schedules agent turns, and analyzes the results. [...]

---

### [0:18 — clicking Talk to the Catalog → Gemma]

> Every Crusoe model in the catalog gets its own character — visual identities generated live by Perfect Corp's text-to-image API. [...] Pick any model, talk to it. The reply you see comes from a real Crusoe inference call to that specific model. [...] Right now I'm asking Gemma 4 31B about multi-model collaboration. [...] Real endpoint. Real model. Real voice.

---

### [0:50 — Beauty tab, clicking Run]

> For Perfect Corp's challenge, the Beauty tab makes a live Skin Analysis API call against a face image. [...] Ten metric scores. Overall skin score. Estimated skin age. [...] ML overlays from Perfect Corp's own pipeline — all in the browser, all in eight seconds. [...] A production-shape consumer experience — not a mockup.

---

### [1:25 — Lark Red Team tab]

> And for Lark's challenge, the dual-agent Gatekeeper survives a 24-attack red team — verified live. 100% A-plus.

---

### [1:30 — closing sim view]

> Resilient agents. Chaos-tested. [...]

---

### [1:34 — end card]

> Four sponsors. Solo entry. All live-verified.

---

## Recording tips

- Don't try to land each line on the exact second — close is fine, the merge nudges it.
- Pause naturally on `[...]` — those are breath beats.
- If a section feels too tight, drop a sentence — everything except the bracketed cues is optional.
- Conversational tone > announcer tone.
- Record at ~16 kHz mono or higher; mp3/m4a/wav all merge fine.

## After recording

1. Save the audio anywhere (e.g. `~/Downloads/voiceover.m4a`).
2. Hand the path back to the assistant — it'll run:
   ```
   ffmpeg -i demo/videos/agent_colosseum_trailer.mp4 -i <audio> \
          -map 0:v -map 1:a -c:v copy -c:a aac -shortest \
          demo/videos/agent_colosseum_trailer_voiced.mp4
   ```
3. The result lands at `demo/videos/agent_colosseum_trailer_voiced.mp4`.
