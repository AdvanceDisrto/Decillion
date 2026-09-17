from matrix.accelerator import best, probe_all, summary


def test_cpu_fallback_is_always_available():
    devices = probe_all()
    assert devices[-1].kind == "cpu"
    assert devices[-1].available
    assert best().available
    assert summary()["platform"]["python"]
