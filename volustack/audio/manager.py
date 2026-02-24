from pycaw.pycaw import (
    AudioUtilities,
    IAudioSessionControl2,
    ISimpleAudioVolume,
)
from pycaw.utils import AudioUtilities as AudioUtils

from volustack.audio.session import AppAudioState, AudioSessionInfo
from volustack.audio.process_helper import get_executable_path, get_process_name
from volustack.audio.icon_cache import IconCache


class AudioManager:
    def __init__(self) -> None:
        self._icon_cache = IconCache()
        self._volume_controls: dict[str, ISimpleAudioVolume] = {}
        self._endpoint_volume = None
        try:
            self._endpoint_volume = AudioUtilities.GetSpeakers().EndpointVolume
        except Exception:
            pass

    def get_master_volume(self) -> float:
        if self._endpoint_volume:
            try:
                return self._endpoint_volume.GetMasterVolumeLevelScalar()
            except Exception:
                pass
        return 1.0

    def set_master_volume(self, volume: float) -> None:
        volume = max(0.0, min(1.0, volume))
        if self._endpoint_volume:
            try:
                self._endpoint_volume.SetMasterVolumeLevelScalar(volume, None)
            except Exception:
                pass

    def enumerate_sessions(self) -> list[AudioSessionInfo]:
        """Enumerate audio sessions from all active render devices.

        Phase 1: collect every non-expired session from every device.
        Phase 2: deduplicate by PID — for each PID keep the best session:
          - Prefer Active over Inactive (Discord voice is Active on Altavoces)
          - Tiebreak: prefer default device (Brave on FxSound controls volume)
        Phase 3: label duplicate executables (Discord noti / voz).
        """
        from collections import defaultdict

        # -- Phase 1: collect all candidates ---------------------------------
        candidates: list[tuple[AudioSessionInfo, ISimpleAudioVolume, bool]] = []

        ordered_devices = self._get_devices_default_first()

        try:
            default_id = AudioUtilities.GetSpeakers().id
        except Exception:
            default_id = None

        for device in ordered_devices:
            is_default = (device.id == default_id)
            try:
                mgr = device.AudioSessionManager
                if mgr is None:
                    continue
                enum = mgr.GetSessionEnumerator()
                count = enum.GetCount()
            except Exception:
                continue

            for i in range(count):
                try:
                    raw = enum.GetSession(i)
                    ctl2 = raw.QueryInterface(IAudioSessionControl2)
                    pid = ctl2.GetProcessId()
                    if pid == 0:
                        continue

                    state_val = ctl2.GetState()
                    state = {
                        0: AppAudioState.INACTIVE,
                        1: AppAudioState.ACTIVE,
                        2: AppAudioState.EXPIRED,
                    }.get(state_val, AppAudioState.EXPIRED)

                    if state == AppAudioState.EXPIRED:
                        continue

                    volume_ctl = raw.QueryInterface(ISimpleAudioVolume)
                    volume = volume_ctl.GetMasterVolume()
                    is_muted = bool(volume_ctl.GetMute())

                    exe_path = get_executable_path(pid)
                    if not exe_path:
                        continue

                    process_name = get_process_name(exe_path, pid)
                    icon = self._icon_cache.get_icon(exe_path)

                    session_id = ctl2.GetSessionIdentifier() or ""
                    if not session_id:
                        continue

                    info = AudioSessionInfo(
                        process_id=pid,
                        process_name=process_name,
                        executable_path=exe_path,
                        session_identifier=session_id,
                        volume=volume,
                        is_muted=is_muted,
                        state=state,
                        icon=icon,
                    )
                    candidates.append((info, volume_ctl, is_default))
                except Exception:
                    continue

        # -- Phase 2: per-PID dedup ------------------------------------------
        by_pid: defaultdict[int, list[tuple[AudioSessionInfo, ISimpleAudioVolume, bool]]] = defaultdict(list)
        for item in candidates:
            by_pid[item[0].process_id].append(item)

        sessions: list[AudioSessionInfo] = []
        new_controls: dict[str, ISimpleAudioVolume] = {}
        session_from_default: dict[str, bool] = {}

        for pid, group in by_pid.items():
            # Sort: Active first (state=1 → sort key 0), then default device first
            group.sort(key=lambda x: (x[0].state != AppAudioState.ACTIVE, not x[2]))
            best_info, best_ctl, best_is_default = group[0]
            sessions.append(best_info)
            new_controls[best_info.session_identifier] = best_ctl
            session_from_default[best_info.session_identifier] = best_is_default

        # -- Phase 3: label duplicates (e.g. Discord noti vs voz) ------------
        from collections import Counter
        exe_counts = Counter(s.executable_path for s in sessions)
        for s in sessions:
            if exe_counts[s.executable_path] > 1:
                s.display_suffix = "noti" if session_from_default.get(s.session_identifier, True) else "voz"

        self._volume_controls = new_controls
        return sessions

    @staticmethod
    def _get_devices_default_first() -> list:
        """Return active render devices with the default device first."""
        try:
            default = AudioUtilities.GetSpeakers()
            default_id = default.id
        except Exception:
            default_id = None

        try:
            all_devices = AudioUtils.GetAllDevices()
            active = [
                d for d in all_devices
                if d.id.startswith("{0.0.0")
                and str(d.state) == "AudioDeviceState.Active"
            ]
        except Exception:
            return []

        # Put default device at the front
        active.sort(key=lambda d: 0 if d.id == default_id else 1)
        return active

    def get_session_volumes(self) -> dict[str, tuple[float, bool]]:
        """Read current volume/mute from cached controls (lightweight, no COM enum)."""
        result: dict[str, tuple[float, bool]] = {}
        for sid, ctl in self._volume_controls.items():
            try:
                vol = ctl.GetMasterVolume()
                muted = bool(ctl.GetMute())
                result[sid] = (vol, muted)
            except Exception:
                pass
        return result

    def set_session_volume(self, session_id: str, volume: float) -> None:
        volume = max(0.0, min(1.0, volume))
        ctl = self._volume_controls.get(session_id)
        if ctl:
            try:
                ctl.SetMasterVolume(volume, None)
            except Exception:
                pass

    def set_session_mute(self, session_id: str, mute: bool) -> None:
        ctl = self._volume_controls.get(session_id)
        if ctl:
            try:
                ctl.SetMute(int(mute), None)
            except Exception:
                pass

    def sleep(self) -> None:
        """Release cached COM controls and icon cache to free memory."""
        self._volume_controls.clear()
        self._icon_cache.clear()
