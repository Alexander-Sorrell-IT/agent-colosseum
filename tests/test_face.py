"""Tests for FaceGenerator — the cache must be load-bearing and the extractor honest."""

import base64
from colosseum.face import FaceGenerator, _extract_image


class FakePerfect:
    """Counts text_to_image calls; returns a result with one base64 image."""
    def __init__(self):
        self.calls = 0
        self._img = base64.b64encode(b"\xff\xd8\xff" + b"x" * 1000).decode()

    def text_to_image(self, prompt, template_id):
        self.calls += 1
        return {"status": "success", "result": {"results": [{"url_or_b64": self._img}]}}


def test_same_face_key_generates_once():
    fake = FakePerfect()
    gen = FaceGenerator(client=fake)
    k = (("m1", "m2"), "mind")
    a = gen.image_for(k, "prompt")
    b = gen.image_for(k, "prompt")
    assert a == b and a is not None
    assert fake.calls == 1            # second call is a cache hit
    assert gen.generations == 1


def test_different_face_key_generates_again():
    fake = FakePerfect()
    gen = FaceGenerator(client=fake)
    gen.image_for((("m1",), "mind"), "p1")
    gen.image_for((("m1", "m2"), "mind"), "p2")   # different active slots
    gen.image_for((("m1",), "m1"), "p3")          # different speaker
    assert fake.calls == 3


def test_disk_cache_survives_new_instance(tmp_path):
    fake = FakePerfect()
    k = (("m1",), "mind")
    g1 = FaceGenerator(client=fake, cache_dir=str(tmp_path))
    g1.image_for(k, "p")
    assert fake.calls == 1
    # fresh generator, same disk cache -> no new API call
    g2 = FaceGenerator(client=fake, cache_dir=str(tmp_path))
    data = g2.image_for(k, "p")
    assert data is not None
    assert fake.calls == 1
    assert g2.generations == 0


def test_failed_generation_not_cached():
    class FailPerfect:
        def __init__(self): self.calls = 0
        def text_to_image(self, prompt, template_id):
            self.calls += 1
            return {"status": "error", "message": "boom"}
    fake = FailPerfect()
    gen = FaceGenerator(client=fake)
    k = (("m1",), "mind")
    assert gen.image_for(k, "p") is None
    assert gen.image_for(k, "p") is None
    assert fake.calls == 2            # not cached, so it retries


def test_client_exception_degrades_to_none():
    # a raising Perfect Corp client must degrade to None, never propagate out of image_for
    class RaisePerfect:
        def text_to_image(self, prompt, template_id):
            raise RuntimeError("perfect corp down")
    gen = FaceGenerator(client=RaisePerfect())
    assert gen.image_for((("m1",), "mind"), "p") is None   # must not raise


def test_extract_image_prefers_base64():
    raw = base64.b64encode(b"\xff\xd8\xff" + b"y" * 800).decode()
    out = _extract_image({"results": [{"image": raw}]})
    assert out is not None and out.startswith(b"\xff\xd8\xff")


def test_extract_image_none_when_absent():
    assert _extract_image({"status": "success", "note": "no image here"}) is None


def test_extract_image_rejects_decodable_junk():
    # a long base64-decodable string that is NOT an image must be rejected, not cached
    junk = "Z" * 640                      # decodes, but no image magic
    assert _extract_image({"results": [{"trace_id": junk}]}) is None


def test_different_templates_do_not_collide(tmp_path):
    fake = FakePerfect()
    k = (("m1",), "mind")
    real = FaceGenerator(client=fake, template_id="style_realistic", cache_dir=str(tmp_path))
    anime = FaceGenerator(client=fake, template_id="style_anime", cache_dir=str(tmp_path))
    real.image_for(k, "p")
    anime.image_for(k, "p")               # same face_key, different template
    assert fake.calls == 2                # must NOT serve the realistic image for anime
    assert real._disk_path(k) != anime._disk_path(k)
