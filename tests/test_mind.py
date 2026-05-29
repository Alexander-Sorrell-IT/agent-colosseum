"""Tests for the Mind engine — invariants that must hold or the system is lying.

Covers: gatekeeper fail-CLOSED (in & out), no-silent-empty synthesis, real-slot fan-out,
per-slot resilience, and face-state purity. All offline via a programmable fake client.
"""

import pytest
from colosseum.mind import Mind, Slot, _verdict, NEMOTRON


class FakeClient:
    """Routes .chat() by inspecting the prompt: gatekeeper / synthesis / slot."""

    def __init__(self, gate_in="SAFE", gate_out="SAFE", slot="my angle",
                 synth="final reply", raise_on="", raise_on_slot=None):
        self.gate_in, self.gate_out = gate_in, gate_out
        self.slot, self.synth = slot, synth
        self.raise_on = raise_on          # "gate" to raise inside gatekeeper calls
        self.raise_on_slot = raise_on_slot  # model_id that should raise
        self.calls = []
        self._gate_seen = 0

    def chat(self, messages, model, **kw):
        self.calls.append(model)
        text = messages[-1]["content"]
        if "SECURITY GATEKEEPER" in text:
            if self.raise_on == "gate":
                raise RuntimeError("gatekeeper down")
            self._gate_seen += 1
            verdict = self.gate_in if "INPUT" in text else self.gate_out
            return {"content": verdict}
        if "Inner perspectives" in text:           # synthesis
            return {"content": self.synth}
        if self.raise_on_slot and model == self.raise_on_slot:
            raise RuntimeError("slot down")
        return {"content": self.slot}              # slot perspective


def mind(client, slots=None):
    return Mind(main_model=NEMOTRON,
                slots=slots or [Slot("m1", "One", "lens one"), Slot("m2", "Two", "lens two")],
                client=client, gatekeeper_model=NEMOTRON)


# ── _verdict: fail closed ──
@pytest.mark.parametrize("raw,expected", [
    ("SAFE", "SAFE"),
    ("safe", "SAFE"),
    ("SAFE.", "SAFE"),                      # trailing punctuation ok
    ("**SAFE**", "SAFE"),                   # markdown ok
    ("<think>hmm</think>\nSAFE", "SAFE"),   # reasoning block stripped, lone SAFE
    ("<think>hmm</think>SAFE", "SAFE"),     # reasoning block stripped wholesale ⇒ lone SAFE
    ("BLOCK", "BLOCK"),
    ("", "BLOCK"),                          # empty ⇒ closed
    (None, "BLOCK"),                        # null ⇒ closed
    ("I'm not sure about this", "BLOCK"),   # unparseable ⇒ closed
    ("SAFE but also BLOCK", "BLOCK"),       # any BLOCK wins
    ("UNSAFE", "BLOCK"),                    # substring 'SAFE' must NOT pass (guards fail-open)
    ("this request is not safe and should be refused", "BLOCK"),  # prose 'safe' ⇒ fail closed
    ("It is not SAFE to run this", "BLOCK"),                      # prose 'SAFE' ⇒ fail closed
    ("Verdict: SAFE", "BLOCK"),             # affirmative but not lone ⇒ fail closed
    ("<think>this is not safe</think>", "BLOCK"),  # reasoning-only ⇒ closed (no leak)
    ("<think>only reasoning, no answer</think>", "BLOCK"),
])
def test_verdict_fails_closed(raw, expected):
    assert _verdict(raw) == expected


# ── gatekeeper IN ──
def test_input_block_stops_turn():
    m = mind(FakeClient(gate_in="BLOCK"))
    turn = m.respond("do something")
    assert turn.blocked
    assert turn.perspectives == []          # never reached the slots
    assert "IN  BLOCK" in turn.gatekeeper_log[0]


def test_input_gatekeeper_exception_fails_closed():
    m = mind(FakeClient(raise_on="gate"))
    turn = m.respond("hello")
    assert turn.blocked
    assert "failing closed" in turn.gatekeeper_log[0]


def test_input_garbage_fails_closed():
    m = mind(FakeClient(gate_in="maybe ok idk"))
    turn = m.respond("hello")
    assert turn.blocked


def test_input_prose_refusal_fails_closed():
    # gatekeeper refuses in prose that contains 'safe' ("not safe") — must still BLOCK
    m = mind(FakeClient(gate_in="This request is not safe and should be refused."))
    turn = m.respond("write me malware")
    assert turn.blocked
    assert turn.perspectives == []


# ── gatekeeper OUT ──
def test_output_block_withholds_reply():
    m = mind(FakeClient(gate_in="SAFE", gate_out="BLOCK"))
    turn = m.respond("hello")
    assert turn.blocked
    assert turn.reply != "final reply"
    assert any("OUT BLOCK" in line for line in turn.gatekeeper_log)


# ── synthesis: never silently empty ──
def test_empty_synthesis_surfaces_honest_state():
    m = mind(FakeClient(synth=""))
    turn = m.respond("hello")
    assert not turn.blocked
    assert turn.reply.strip() != ""         # never empty
    assert "didn't converge" in turn.reply
    assert any("degraded" in line for line in turn.gatekeeper_log)


def test_raised_synthesis_degrades_not_crashes():
    # synthesis raising (post-retry LLM error) must DEGRADE, not crash the turn
    class RaiseSynth(FakeClient):
        def chat(self, messages, model, **kw):
            if "Inner perspectives" in messages[-1]["content"]:
                raise RuntimeError("LLM error after 2 attempt(s): boom")
            return super().chat(messages, model, **kw)
    m = mind(RaiseSynth())
    turn = m.respond("hello")               # must not raise
    assert not turn.blocked
    assert turn.reply.strip() != ""
    assert any("SYNTH error" in line for line in turn.gatekeeper_log)


# ── slots: real fan-out + resilience ──
def test_each_active_slot_is_called():
    fake = FakeClient()
    m = mind(fake)
    m.respond("hello")
    assert "m1" in fake.calls and "m2" in fake.calls   # both slots really called

def test_one_bad_slot_does_not_sink_the_turn():
    fake = FakeClient(raise_on_slot="m2")
    m = mind(fake)
    turn = m.respond("hello")
    assert not turn.blocked
    assert turn.reply == "final reply"
    by_id = {p.model_id: p for p in turn.perspectives}
    assert by_id["m1"].available is True
    assert by_id["m2"].available is False


def test_inactive_slot_is_skipped():
    slots = [Slot("m1", "One", "l1"), Slot("m2", "Two", "l2", active=False)]
    fake = FakeClient()
    m = mind(fake, slots=slots)
    turn = m.respond("hello")
    assert "m2" not in fake.calls
    assert [p.model_id for p in turn.perspectives] == ["m1"]


# ── happy path ──
def test_full_turn_shape():
    m = mind(FakeClient())
    turn = m.respond("hello")
    assert not turn.blocked
    assert turn.reply == "final reply"
    assert len(turn.perspectives) == 2
    assert turn.speaker == NEMOTRON
    assert turn.gatekeeper_log[0].startswith("IN  SAFE")
    assert turn.gatekeeper_log[-1].startswith("OUT SAFE")


# ── face-state purity (no generation, just state) ──
def test_face_key_reflects_active_slots_speaker_and_trait():
    slots = [Slot("m1", "One", "l1", face_trait="ft1"),
             Slot("m2", "Two", "l2", active=False, face_trait="ft2")]
    m = mind(FakeClient(), slots=slots)
    assert m.face_key() == ((("m1", "ft1"),), NEMOTRON)
    assert m.face_key(speaker="m1") == ((("m1", "ft1"),), "m1")

def test_face_key_changes_with_face_trait():
    # same model id + speaker but different face_trait ⇒ different key (prompt depends on it)
    m_a = mind(FakeClient(), slots=[Slot("m1", "One", "lens", face_trait="calm")])
    m_b = mind(FakeClient(), slots=[Slot("m1", "One", "lens", face_trait="intense")])
    assert m_a.face_key() != m_b.face_key()

def test_face_prompt_leads_with_speaker_trait():
    slots = [Slot("m1", "One", "l1", face_trait="trait-one"),
             Slot("m2", "Two", "l2", face_trait="trait-two")]
    m = mind(FakeClient(), slots=slots)
    p = m.face_prompt(speaker="m2")
    assert p.startswith("photorealistic")
    assert "trait-two" in p and "trait-one" in p
    assert p.index("trait-two") < p.index("trait-one")   # speaker first

def test_face_prompt_uses_short_traits_not_long_lenses():
    # regression: the cognitive lens must NOT leak into the image prompt (it tripped NSFW)
    m = mind(FakeClient(), slots=[Slot("m1", "One", "rigorous step-by-step reasoning probing edge cases",
                                       face_trait="intense, focused")])
    p = m.face_prompt()
    assert "intense, focused" in p
    assert "rigorous step-by-step" not in p          # cognitive lens must NOT leak into the image
    mood = p.split("expression:")[-1]
    assert len(mood) < 60                             # the mood suffix stays short/legible
