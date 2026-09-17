"""Optional accelerator discovery with a dependency-free CPU fallback."""

from __future__ import annotations

import importlib
import json
import os
import platform
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Device:
    kind: str
    torch_name: object
    label: str
    available: bool
    enable: str = ""


def _torch():
    try:
        return importlib.import_module("torch")
    except ImportError:
        return None


def _cuda(torch) -> Device:
    if torch is not None and torch.cuda.is_available():
        return Device("cuda", "cuda", f"CUDA: {torch.cuda.get_device_name(0)}", True)
    return Device("cuda", "cpu", "CUDA", False, "install a CUDA-enabled PyTorch build")


def _mps(torch) -> Device:
    available = bool(
        torch is not None and hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    )
    return Device(
        "mps", "mps" if available else "cpu", "Apple MPS", available, "requires Apple Silicon"
    )


def _directml() -> Device:
    try:
        directml = importlib.import_module("torch_directml")
        if directml.device_count() > 0:
            return Device("directml", directml.device(0), "DirectML", True)
    except (ImportError, RuntimeError):
        pass
    return Device("directml", "cpu", "DirectML", False, "install torch-directml on Windows")


def _tpu() -> Device:
    try:
        importlib.import_module("torch_xla")
        return Device("tpu", "xla", "Google TPU", True)
    except ImportError:
        return Device("tpu", "cpu", "Google TPU", False, "install torch_xla on a TPU VM")


def _cpu(torch) -> Device:
    threads = torch.get_num_threads() if torch is not None else (os.cpu_count() or 1)
    return Device("cpu", "cpu", f"CPU ({threads} threads)", True)


def probe_all() -> list[Device]:
    torch = _torch()
    return [_cuda(torch), _mps(torch), _directml(), _tpu(), _cpu(torch)]


def best() -> Device:
    return next(device for device in probe_all() if device.available)


def summary() -> dict:
    devices = probe_all()
    return {
        "best": asdict(next(device for device in devices if device.available)),
        "all": [asdict(device) for device in devices],
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
    }


def main() -> None:
    print(json.dumps(summary(), indent=2, default=str))


if __name__ == "__main__":
    main()
