from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

import yaml
from obswebsocket.base_classes import Baserequests
from quart import current_app

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


log = logging.getLogger(__name__)


FFMPEG_SOURCE = "ffmpeg_source"

logging.basicConfig(level=logging.INFO)

from obswebsocket import obsws, requests  # noqa: E402


class Connection:
    def __init__(self):
        host = "localhost"
        port = 4444
        password = "sleuth"
        self.started = False

        self.ws = obsws(host, port, password)

    def call(self, request: Baserequests) -> Baserequests:
        self._ensure_connected()
        return self.ws.call(request)

    def _ensure_connected(self):
        if self.started:
            return

        self.ws.connect()
        self.started = True

    def set_video(self, source: str, path):
        self.call(
            requests.SetSourceSettings(
                sourceName=source,
                sourceType=FFMPEG_SOURCE,
                sourceSettings=dict(
                    local_file=path,
                ),
            )
        )

    def show_scene(self, scene: str):
        self.call(requests.SetCurrentScene(scene))

    def toggle_credits(self, show: bool):
        self.call(requests.SetSceneItemProperties("Credits", visible=show))

    def set_credits(self, link: str):
        self.call(requests.SetTextFreetype2Properties("Credits", text=link))

    def set_up_next(self, title):
        self.call(
            requests.SetTextFreetype2Properties(
                "Text: Up next", text=f"Up next: {title}"
            )
        )

    def set_news_ticker(self, headlines: List[str]):
        length = 0
        max_length = 1024
        for idx, title in enumerate(headlines):
            if len(title) + length > max_length:
                text = "     ".join(headlines[0 : idx - 1])
                break
            length += len(title)
        else:
            text = "     ".join(headlines)

        self.call(requests.SetTextFreetype2Properties("News ticker", text=text))
