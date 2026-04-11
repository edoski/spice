from __future__ import annotations

from spice.core.power import keep_system_awake


class _DummyProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.wait_calls: list[float | None] = []

    def poll(self) -> None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout: float | None = None) -> None:
        self.wait_calls.append(timeout)

    def kill(self) -> None:
        self.killed = True


def test_keep_system_awake_is_noop_off_macos(monkeypatch) -> None:
    popen_called = False
    monkeypatch.setattr("spice.core.power.sys.platform", "linux")
    monkeypatch.setattr(
        "spice.core.power.subprocess.Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected Popen call")),
    )

    with keep_system_awake():
        popen_called = True

    assert popen_called is True


def test_keep_system_awake_launches_caffeinate_on_macos(monkeypatch) -> None:
    process = _DummyProcess()
    recorded: list[list[str]] = []

    monkeypatch.setattr("spice.core.power.sys.platform", "darwin")
    monkeypatch.setattr("spice.core.power.shutil.which", lambda name: "/usr/bin/caffeinate")
    monkeypatch.setattr("spice.core.power.os.getpid", lambda: 4321)

    def _fake_popen(cmd, **kwargs):
        recorded.append(cmd)
        return process

    monkeypatch.setattr("spice.core.power.subprocess.Popen", _fake_popen)

    with keep_system_awake():
        pass

    assert recorded == [["/usr/bin/caffeinate", "-i", "-w", "4321"]]
    assert process.terminated is True
    assert process.wait_calls == [1]
    assert process.killed is False
