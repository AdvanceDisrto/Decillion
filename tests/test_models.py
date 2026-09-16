import pytest

from decillion import models
from decillion.errors import LicensePolicyError
from decillion.models import discover, mirror, normalize_license, require_license


def test_license_normalization():
    assert normalize_license("MIT") == "mit"
    assert normalize_license("Apache 2.0") == "apache-2.0"


def test_license_policy_fails_closed():
    assert require_license("MIT", "mit") == "mit"
    with pytest.raises(LicensePolicyError):
        require_license("modified-mit", "mit")
    with pytest.raises(LicensePolicyError):
        require_license(None, "mit")


class FakeModel:
    id = "org/model"
    sha = "abc123"
    downloads = 42
    card_data = {"license": "mit"}


class FakeApi:
    def list_models(self, **kwargs):
        assert kwargs["filter"] == "license:mit"
        return [FakeModel()]

    def model_info(self, model_id, files_metadata=False):
        assert model_id == "org/model"
        assert files_metadata is False
        return FakeModel()


def fake_snapshot_download(**kwargs):
    return str(kwargs["local_dir"])


def test_discover_and_mirror(monkeypatch, tmp_path):
    monkeypatch.setattr(models, "_hub", lambda: (FakeApi(), fake_snapshot_download))
    records = discover("mit", 10)
    assert records[0].model_id == "org/model"
    metadata = mirror("org/model", "mit", tmp_path, False)
    assert metadata["revision"] == "abc123"
    assert metadata["downloaded_weights"] is False
    downloaded = mirror("org/model", "mit", tmp_path, True)
    assert downloaded["downloaded_weights"] is True
    assert "org/model" in downloaded["destination"]


def test_hub_dependency_message(monkeypatch):
    original = __import__

    def blocked(name, *args, **kwargs):
        if name == "huggingface_hub":
            raise ImportError("blocked")
        return original(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked)
    with pytest.raises(SystemExit):
        models._hub()
