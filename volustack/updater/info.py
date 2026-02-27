from dataclasses import dataclass


@dataclass
class UpdateInfo:
    version: str
    download_url: str | None = None
    asset_name: str | None = None
    file_size: int = 0
    release_notes: str = ""
    published_at: str = ""
