from __future__ import annotations

import logging
from typing import List

from obsws_python import ReqClient

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


log = logging.getLogger(__name__)


FFMPEG_SOURCE = "ffmpeg_source"

logging.basicConfig(level=logging.INFO)


class Connection:
    def __init__(self):
        host = "localhost"
        port = 4455
        password = "KMa460AdpjifR5f5"

        self.obs = ReqClient(host=host,
                             port=port,
                             password=password,
                             timeout=3)
        self.started = True

    def set_video(self, source: str, path):
        self.obs.set_input_settings(name=source, settings=dict(local_file=path), overlay=False)

    def show_scene(self, scene: str):
        self.obs.set_current_program_scene(name=scene)

    def toggle_credits(self, scene_name: str, show: bool):
        resp = self.obs.get_scene_item_id(
            scene_name=scene_name,
            source_name="Credits",
        )
        self.obs.set_scene_item_enabled(
            scene_name=scene_name,
            item_id=resp.scene_item_id,
            enabled=show,
        )

    def set_credits(self, link: str):
        self.obs.set_input_settings(
            name="Credits", settings=dict(text=link), overlay=True
        )

    def set_up_next(self, title):
        self.obs.set_input_settings(
            name="Up next", settings=dict(text=f"Up next: {title}"), overlay=True
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

        self.obs.set_input_settings(
            name="News ticker", settings=dict(text=text), overlay=True
        )
