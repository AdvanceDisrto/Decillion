import hashlib

from main import app, canonical


def test_canonical_stable():
    assert canonical({"b": 2, "a": 1}) == b'{"a":1,"b":2}'


def test_sha256_stable():
    assert hashlib.sha256(canonical({"a": 1})).hexdigest() == (
        "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )


def test_routes_exist():
    paths = {r.path for r in app.routes}
    assert {"/health", "/v1/actions", "/v1/receipts"}.issubset(paths)
