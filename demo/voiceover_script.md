# Agent Colosseum — Trailer Voiceover Script

**Target length:** ~95 seconds (matches `demo/videos/agent_colosseum_trailer.mp4`)
**Word count:** ~200 (≈150 wpm with breath beats)
**Tone:** engineer talking about their work — concrete, unhyped, first-person

`[…]` marks are natural breath beats. `[mm:ss]` cues match the trailer timeline.

---

### [0:00 — title card]

> This is Agent Colosseum.

---

### [0:04 — Sim landing, agent table appears]

> It started with one Crusoe API key. Seven models behind it. [...] Most hackathon entries pick one and build a chat box. I wanted to know what happens when you make all seven work together. [...] So Nemotron Super-120B isn't answering questions here — it's running the whole simulation.

---

### [0:18 — clicking Talk to the Catalog → Gemma → typing → reply]

> Every model in the catalog has its own face — generated live by Perfect Corp's text-to-image API. [...] I'm clicking Gemma 4 31B and asking it about multi-model collaboration. [...] The reply you see is a real Crusoe inference call. [...] Same flow for any of the seven models. Pick one, talk to it, get a real answer from the actual endpoint.

---

### [0:50 — Beauty tab, clicking Run, scores rendering]

> For Perfect Corp's challenge, the Beauty tab takes a face and runs a live skin analysis. [...] Ten metric scores. Estimated skin age. ML overlays straight from their pipeline. [...] About eight seconds, every time. That's the consumer flow their brief asks for — not a mockup.

---

### [1:25 — Lark Red Team tab]

> For Lark, the dual-agent gatekeeper takes 24 attacks. Twenty blocked, four allowed, zero false positives.

---

### [1:30 — closing sim view]

> For TrueFoundry — chaos injection, retries, fail-closed.

---

### [1:34 — end card]

> Solo, four sponsors, verified live.

---

## Recording tips

- Don't chase the seconds — close is fine, the merge nudges timing.
- Pause naturally on `[...]` — those are breath beats.
- If something feels too tight, drop a sentence — everything except `[mm:ss]` cues is optional.
- Conversational. Not announcer.
- Mic ~30cm. mp3 / m4a / wav all merge fine.

## After recording

1. Save the audio anywhere (e.g. `~/Downloads/voiceover.m4a`).
2. Give the path to the assistant — it'll run:
   ```
   ffmpeg -i demo/videos/agent_colosseum_trailer.mp4 -i <audio> \
          -map 0:v -map 1:a -c:v copy -c:a aac -shortest \
          demo/videos/agent_colosseum_trailer_voiced.mp4
   ```
3. Result: `demo/videos/agent_colosseum_trailer_voiced.mp4`.
