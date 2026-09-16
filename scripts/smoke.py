#!/usr/bin/env python3
import os
import tempfile
from pathlib import Path

from decillion.engine import SovereignStorage
from decillion.keys import LocalKeyProvider
from decillion.objects import FileObjectStore
from decillion.receipts import ReceiptSigner, merkle_root, verify_receipt


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        engine = SovereignStorage(
            FileObjectStore(Path(temp) / "objects"),
            LocalKeyProvider(os.urandom(32)),
            ReceiptSigner.generate(),
        )
        values = []
        for index in range(10):
            content = f"receipt-{index}".encode()
            receipt = engine.upload("smoke-wallet", f"{index}.txt", content).receipt
            verify_receipt(receipt, engine.signer.public_key)
            actual = engine.download(receipt, owner="smoke-wallet", filename=f"{index}.txt")
            assert actual == content
            values.append(receipt)
        root = merkle_root(values)
        assert len(root) == 64
        print(f"DECILLION_SMOKE_PASS objects=10 merkle_root={root}")


if __name__ == "__main__":
    main()
