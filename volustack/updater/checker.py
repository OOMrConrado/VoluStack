import requests
from packaging.version import Version

from volustack.updater.info import UpdateInfo

REPO_OWNER = "OOMrConrado"
REPO_NAME = "VoluStack"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
ASSET_NAME = "VoluStack-Setup.exe"


class UpdateChecker:
    def __init__(self, current_version: str) -> None:
        self.current_version = current_version

    def check_for_updates(self) -> UpdateInfo | None:
        try:
            resp = requests.get(
                API_URL,
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            tag_name: str = data["tag_name"]
            latest_version = tag_name.lstrip("v")

            if Version(latest_version) <= Version(self.current_version):
                return None

            target_asset = None
            for asset in data.get("assets", []):
                if asset.get("name") == ASSET_NAME:
                    target_asset = asset
                    break

            return UpdateInfo(
                version=latest_version,
                download_url=(
                    target_asset["browser_download_url"]
                    if target_asset
                    else data.get("html_url")
                ),
                asset_name=target_asset["name"] if target_asset else None,
                file_size=target_asset.get("size", 0) if target_asset else 0,
                release_notes=data.get("body", ""),
                published_at=data.get("published_at", ""),
            )
        except Exception:
            return None
