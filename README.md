# VoluStack

Per-application volume control for Windows. A lightweight desktop utility that gives you individual volume sliders for each running application, accessible via a floating window or system tray.


## Features

- **Per-app volume control** — Individual volume sliders for each application playing audio
- **Master volume** — Quick access to system master volume
- **System tray** — Minimize to tray, always accessible
- **Global hotkey** — Toggle window with `Ctrl+Shift+V` (customizable)
- **Multi-device support** — Handles multiple audio output devices
- **Auto-updater** — Checks for new releases from GitHub
- **Sleep mode** — Near-zero resource usage when the window is hidden
- **Dark UI** — Frameless floating window with a modern dark theme

## Installation

### Installer (Recommended)

Download the latest `VoluStack-Setup.exe` from [Releases](https://github.com/OOMrConrado/VoluStack/releases).



## Usage

- **Open/close** the window: press `Ctrl+Shift+V` or click the tray icon
- **Expand** the session list with the chevron button
- **Adjust** individual app volumes with the sliders
- **Mute** an app by clicking its speaker icon
- **Settings** via the gear icon — customize the hotkey, check for updates

Run with:

```bash
python main.py
```


## Project Structure

```
volustack/
  audio/        WASAPI audio session control (pycaw)
  ui/           PyQt6 widgets and window
  tray/         System tray service
  hotkey/       Global hotkey service
  settings/     JSON settings persistence
  updater/      GitHub releases auto-updater
  main.py       Application entry point
  version.py    Version string
```

## License

[MIT](LICENSE)
