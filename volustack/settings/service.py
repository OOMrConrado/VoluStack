import json
import os


_DEFAULTS: dict[str, object] = {
    "minimize_to_tray": True,
    "start_with_windows": False,
    "auto_check_updates": True,
    "hotkey_modifiers": "ctrl+shift",
    "hotkey_key": "v",
}


class SettingsService:
    def __init__(self) -> None:
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        self._dir = os.path.join(appdata, "VoluStack")
        self._path = os.path.join(self._dir, "settings.json")
        self._data: dict[str, object] = self._load()

    def _load(self) -> dict[str, object]:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r") as f:
                    return {**_DEFAULTS, **json.load(f)}
            except (json.JSONDecodeError, OSError):
                pass
        return dict(_DEFAULTS)

    def save(self) -> None:
        os.makedirs(self._dir, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def minimize_to_tray(self) -> bool:
        return bool(self._data.get("minimize_to_tray", True))

    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool) -> None:
        self._data["minimize_to_tray"] = value
        self.save()

    @property
    def start_with_windows(self) -> bool:
        return bool(self._data.get("start_with_windows", False))

    @start_with_windows.setter
    def start_with_windows(self, value: bool) -> None:
        self._data["start_with_windows"] = value
        self.save()

    @property
    def auto_check_updates(self) -> bool:
        return bool(self._data.get("auto_check_updates", True))

    @auto_check_updates.setter
    def auto_check_updates(self, value: bool) -> None:
        self._data["auto_check_updates"] = value
        self.save()

    @property
    def hotkey_modifiers(self) -> str:
        return str(self._data.get("hotkey_modifiers", "ctrl+shift"))

    @hotkey_modifiers.setter
    def hotkey_modifiers(self, value: str) -> None:
        self._data["hotkey_modifiers"] = value
        self.save()

    @property
    def hotkey_key(self) -> str:
        return str(self._data.get("hotkey_key", "v"))

    @hotkey_key.setter
    def hotkey_key(self, value: str) -> None:
        self._data["hotkey_key"] = value
        self.save()

    @property
    def hotkey_combo(self) -> str:
        return f"{self.hotkey_modifiers}+{self.hotkey_key}"
