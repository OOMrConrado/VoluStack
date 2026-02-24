from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtGui import QPixmap


class AppAudioState(Enum):
    ACTIVE = 1
    INACTIVE = 2
    EXPIRED = 0


@dataclass
class AudioSessionInfo:
    process_id: int
    process_name: str
    executable_path: str
    session_identifier: str
    volume: float
    is_muted: bool
    state: AppAudioState
    icon: QPixmap | None = field(default=None, repr=False)
    display_suffix: str = ""  # e.g. "voz", "noti" for duplicate process names
