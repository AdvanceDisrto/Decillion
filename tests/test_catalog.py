from decillion.catalog import ReceiptCatalog
from decillion.receipts import Receipt


def sample(object_id="a" * 64):
    return Receipt(
        1,
        object_id,
        "wallet",
        "b" * 64,
        1,
        40,
        "2026-01-01T00:00:00+00:00",
        "wrapped",
        "sig",
    )


def test_catalog_round_trip(tmp_path):
    catalog = ReceiptCatalog(tmp_path / "receipts.db")
    receipt = sample()
    catalog.add(receipt)
    assert catalog.get(receipt.object_id) == receipt
    assert catalog.list_owner("wallet") == [receipt]
    assert catalog.get("f" * 64) is None
