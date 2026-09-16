import json
import sys

from decillion import cli, models
from decillion.models import ModelRecord


def test_key_cli(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["decillion", "generate-master-key"])
    cli.main()
    assert len(capsys.readouterr().out.strip()) == 44


def test_model_discover_cli(monkeypatch, tmp_path, capsys):
    record = ModelRecord("org/model", "sha", "mit", 1, "now")
    monkeypatch.setattr(models, "discover", lambda license_name, limit: [record])
    output = tmp_path / "catalog.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "decillion-models",
            "discover",
            "--license",
            "mit",
            "--limit",
            "1",
            "--output",
            str(output),
        ],
    )
    models.main()
    assert json.loads(output.read_text())[0]["model_id"] == "org/model"
    assert '"models": 1' in capsys.readouterr().out


def test_model_mirror_cli(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        models,
        "mirror",
        lambda *args: {"model_id": args[0], "downloaded_weights": False},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "decillion-models",
            "mirror",
            "org/model",
            "--license",
            "mit",
            "--destination",
            str(tmp_path),
        ],
    )
    models.main()
    assert "org/model" in capsys.readouterr().out
