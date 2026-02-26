"""Manage VoluStack auto-start via the Windows Registry."""

import sys
import winreg

_RUN_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "VoluStack"


def _exe_command() -> str:
    """Return the command string to register for auto-start."""
    if getattr(sys, "frozen", False):
        # PyInstaller-built .exe
        return f'"{sys.executable}" --minimized'
    # Development mode: python -m volustack
    return f'"{sys.executable}" -m volustack --minimized'


def is_startup_enabled() -> bool:
    """Check if VoluStack is registered to start with Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except FileNotFoundError:
        return False


def set_startup_enabled(enabled: bool) -> None:
    """Add or remove the VoluStack auto-start registry entry."""
    if enabled:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _exe_command())
    else:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, _VALUE_NAME)
        except FileNotFoundError:
            pass
