import psutil

CLEAN_NAMES: dict[str, str] = {
    "chrome": "Google Chrome",
    "msedge": "Microsoft Edge",
    "firefox": "Firefox",
    "spotify": "Spotify",
    "discord": "Discord",
    "teams": "Microsoft Teams",
    "vlc": "VLC Media Player",
    "wmplayer": "Windows Media Player",
    "brave": "Brave Browser",
    "opera": "Opera",
    "steam": "Steam",
    "steamwebhelper": "Steam",
}


def get_executable_path(pid: int) -> str:
    if pid == 0:
        return ""
    try:
        return psutil.Process(pid).exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def get_process_name(executable_path: str, pid: int) -> str:
    if not executable_path:
        return f"Unknown ({pid})"
    file_name = executable_path.rsplit("\\", 1)[-1]
    name = file_name.removesuffix(".exe").removesuffix(".EXE")
    return CLEAN_NAMES.get(name.lower(), name)
