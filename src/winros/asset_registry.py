from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from winros.config import paths


@dataclass(frozen=True)
class AssetDefinition:
    name: str
    track: str
    kind: str
    robot: str
    source: str
    repo_url: str
    local_repo: Path
    model_path: str
    license: str
    priority: str
    notes: str

    @property
    def expected_model_path(self) -> Path | None:
        if not self.model_path:
            return None
        return self.local_repo / self.model_path

    @property
    def is_available(self) -> bool:
        model_path = self.expected_model_path
        if model_path is None:
            return self.local_repo.exists()
        return model_path.exists()


def _asset_config_path() -> Path:
    return paths().configs / "assets" / "open_source_assets.yaml"


def _root_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return paths().root / candidate


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return data


def list_assets(track: str | None = None) -> list[AssetDefinition]:
    data = _load_yaml(_asset_config_path())
    items = data.get("assets", [])
    if not isinstance(items, list):
        raise ValueError("configs/assets/open_source_assets.yaml must contain an assets list")

    assets: list[AssetDefinition] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each asset entry must be a mapping")
        asset = AssetDefinition(
            name=str(item["name"]),
            track=str(item["track"]),
            kind=str(item["kind"]),
            robot=str(item["robot"]),
            source=str(item["source"]),
            repo_url=str(item["repo_url"]),
            local_repo=_root_path(str(item["local_repo"])),
            model_path=str(item.get("model_path") or ""),
            license=str(item["license"]),
            priority=str(item["priority"]),
            notes=str(item.get("notes") or ""),
        )
        if track is None or asset.track in {track, "all"}:
            assets.append(asset)

    return sorted(assets, key=lambda asset: (asset.track, asset.priority, asset.name))


def get_asset(name: str) -> AssetDefinition:
    for asset in list_assets():
        if asset.name == name:
            return asset
    known = ", ".join(asset.name for asset in list_assets())
    raise ValueError(f"Unknown asset '{name}'. Known assets: {known}")
