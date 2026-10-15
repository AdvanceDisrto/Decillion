"""Model registry tests assert capability reporting, not imagined checkpoints."""
import asyncio
from imodels import IDS, configured, registry

def test_model_names():
    assert set(IDS)=={"buddy","the-one"}

def test_registry_does_not_forge_weight_attestation():
    result=asyncio.run(registry())
    assert result["models"]
    assert all(model["weights_verified"] is False for model in result["models"])
    assert all(model["inference_verified"] is False for model in result["models"])

def test_unconfigured_model_is_not_ready():
    if not IDS["buddy"]:
        assert configured("buddy") is False
