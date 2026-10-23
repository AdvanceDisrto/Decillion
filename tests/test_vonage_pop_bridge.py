import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ed25519

sys.path.insert(0, str(Path(__file__).parents[1] / "proof-process"))

from vonage_pop_bridge import (
    mint_signed_receipt,
    verify_vonage_receipt,
)


def test_signature_binds_vonage_response() -> None:
    key = ed25519.Ed25519PrivateKey.generate()
    receipt = mint_signed_receipt(
        channel="sms",
        vonage_response={"message_uuid": "real-or-recorded", "status": "submitted"},
        signer_priv=key,
        signer_id="iRn-test",
    )
    assert verify_vonage_receipt(receipt)["ok"]

    receipt["vonage_response"]["status"] = "delivered"
    assert not verify_vonage_receipt(receipt)["ok"]


def test_t0_limitation_is_mandatory() -> None:
    key = ed25519.Ed25519PrivateKey.generate()
    receipt = mint_signed_receipt(
        channel="sms",
        vonage_response={"message_uuid": "x", "status": "submitted"},
        signer_priv=key,
        signer_id="iRn-test",
        signer_tier="T0",
    )
    assert any("software" in item.lower() for item in receipt["does_not_prove"])
