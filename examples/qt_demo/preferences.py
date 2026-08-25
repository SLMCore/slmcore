"""Small JSON-backed host preference store for the standalone demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DemoPreferences:
    """Persist setup-level preferences expected by ``SLMHostServices``."""

    SCHEMA_VERSION = 1

    def __init__(self,data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self.path = self.data_dir / "preferences.json"
        self._data = self._load()

    def get_startup_config(self,slm_key: str) -> str | None:
        value = self._slm(slm_key).get("startup_config")
        return None if not value else str(value)

    def set_startup_config(self,slm_key: str,value: str | None) -> None:
        entry = self._slm(slm_key)
        if value:
            entry["startup_config"] = str(value)
        else:
            entry.pop("startup_config",None)
        self._save()

    def get_default_plane(self,slm_key: str,section_key: str) -> str | None:
        planes = self._slm(slm_key).get("default_planes",{})
        value = planes.get(section_key) if isinstance(planes,dict) else None
        return None if not value else str(value)

    def set_default_plane(
        self,slm_key: str,section_key: str,value: str | None,
    ) -> None:
        entry = self._slm(slm_key)
        planes = entry.setdefault("default_planes",{})
        if value:
            planes[str(section_key)] = str(value)
        else:
            planes.pop(str(section_key),None)
        if not planes:
            entry.pop("default_planes",None)
        self._save()

    def get_section_display_mode(self,slm_key: str) -> str | None:
        value = self._slm(slm_key).get("section_display_mode")
        return None if not value else str(value)

    def set_section_display_mode(self,slm_key: str,value: Any) -> None:
        entry = self._slm(slm_key)
        normalized = getattr(value,"value",value)
        if normalized:
            entry["section_display_mode"] = str(normalized)
        else:
            entry.pop("section_display_mode",None)
        self._save()

    def _slm(self,slm_key: str) -> dict[str,Any]:
        slms = self._data.setdefault("slms",{})
        return slms.setdefault(str(slm_key),{})

    def _load(self) -> dict[str,Any]:
        if not self.path.is_file():
            return {"schema_version":self.SCHEMA_VERSION,"slms":{}}
        try:
            with self.path.open("r",encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError,json.JSONDecodeError) as error:
            raise RuntimeError(
                "Could not read demo preferences from %s" % self.path
            ) from error
        if not isinstance(value,dict):
            raise ValueError("Demo preferences root must be a JSON object")
        version = value.get("schema_version",self.SCHEMA_VERSION)
        if version != self.SCHEMA_VERSION:
            raise ValueError(
                "Unsupported demo preferences schema version: %r" % version
            )
        slms = value.get("slms",{})
        if not isinstance(slms,dict):
            raise ValueError("Demo preferences 'slms' entry must be an object")
        value["schema_version"] = self.SCHEMA_VERSION
        value["slms"] = slms
        return value

    def _save(self) -> None:
        temporary = self.path.with_suffix(".json.tmp")
        with temporary.open("w",encoding="utf-8") as handle:
            json.dump(self._data,handle,indent=2,sort_keys=True)
            handle.write("\n")
        temporary.replace(self.path)
