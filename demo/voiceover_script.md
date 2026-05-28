# Agent Colosseum — Trailer Voiceover Script

**Target:** ~85 seconds of speech inside the 95s trailer (4s title silence at start, 5s end-card silence at end).
**Word count:** ~140 — deliberately sparse. Trailer voice, not pitch voice.
**Tone:** declarative, atmospheric, confident. Long pauses. The visuals carry weight; the voice doesn't narrate every beat.

The script does not say "for Perfect Corp" or "for Lark" or "solo entry" or "four sponsors." Judges see all that in the visuals and on the Devpost page. The trailer is for the *product*.

---

## The script

> Most AI products live inside one model.
>
> This one lives between seven.
>
> [...]
>
> Nemotron Super runs the room. It picks who acts, when, and what they hear.
>
> [...]
>
> Every model has a face. Click one — you're talking to it directly. Real call. Real model. Real response.
>
> [...]
>
> Hand it a face. Ten metric scores come back. Real overlays. Eight seconds. No mockups, no canned data.
>
> [...]
>
> Twenty-four adversarial attacks against the gatekeeper. Twenty blocked. Four legitimate ones allowed through. None bypass.
>
> [...]
>
> When the infrastructure breaks, the system breaks gracefully. Calls retry. The gatekeeper fails closed. Agents adapt.
>
> [...]
>
> Seven models. One API key.
>
> Working as one.

---

## What's on screen as you say each part (reference, don't read aloud)

| When you're saying | The video is showing |
|---|---|
| "Most AI products live inside one model… between seven." | Title card → Sim landing with agent table |
| "Nemotron Super runs the room…" | Sim landing — host card + Nemotron Super avatar |
| "Every model has a face. Click one — you're talking to it directly." | Talk-to-the-Catalog gallery → click Gemma → typing |
| "Real call. Real model. Real response." | Gemma reply lands on screen |
| "Hand it a face. Ten metric scores come back." | Beauty tab opens → click Run → scores render |
| "Real overlays. Eight seconds." | Beauty overlays close-up |
| "Twenty-four adversarial attacks against the gatekeeper…" | Lark Red Team tab visible |
| "Twenty blocked. Four legitimate allowed through. None bypass." | (hold the beat on the Lark tab) |
| "When the infrastructure breaks…" | Back to Sim view — closing |
| "Seven models. One API key. Working as one." | End card |

---

## How to deliver it

- **Slow the pace.** Trailer voice runs at maybe 110 effective words per minute — closer to half-speed than normal conversation.
- **Let the pauses hang.** The `[...]` marks are where the visuals breathe. Two to three seconds each. Don't fill them.
- **Drop your pitch.** End on the period, not a question.
- **Don't sell.** The product is shown. Your job is to land the line.
- **Avoid emphasis on every word.** Pick the one or two words per sentence that carry the load — usually the noun. "Most AI products live inside one model." The weight is on *one*.

## How to record

- Mic ~30 cm. Quiet room. mp3 / m4a / wav all merge fine.
- Two takes is normal. The second one is almost always better — by then you've stopped reading.
- Try reading it once, then close the doc and re-tell it from memory. That take usually beats the read.

## After recording

1. Save the audio anywhere (e.g. `~/Downloads/voiceover.m4a`).
2. Give the path to the assistant. It runs:
   ```
   ffmpeg -i demo/videos/agent_colosseum_trailer.mp4 -i <audio> \
          -map 0:v -map 1:a -c:v copy -c:a aac -shortest \
          demo/videos/agent_colosseum_trailer_voiced.mp4
   ```
3. Result lands at `demo/videos/agent_colosseum_trailer_voiced.mp4`, ready for Devpost upload.
