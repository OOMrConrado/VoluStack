import os
import subprocess
import sys
import tempfile
from typing import Callable

import requests


class UpdateService:
    def download_update(
        self,
        download_url: str,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> str | None:
        try:
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, "VoluStack-Update.exe")

            resp = requests.get(download_url, stream=True, timeout=60)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            received = 0

            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    received += len(chunk)
                    if on_progress and total > 0:
                        on_progress(received, total)

            return file_path
        except Exception:
            return None

    def install_update(self, installer_path: str, silent: bool = True) -> None:
        args = [installer_path]
        if silent:
            args += ["/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"]

        subprocess.Popen(
            args,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        import time
        time.sleep(1)
        sys.exit(0)

    def cleanup_temp_installers(self) -> None:
        temp_dir = tempfile.gettempdir()
        for entry in os.scandir(temp_dir):
            if entry.is_file() and "VoluStack-Update" in entry.name:
                try:
                    os.remove(entry.path)
                except OSError:
                    pass
