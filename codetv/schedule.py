from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from enum import Enum
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional

import yaml
from quart import current_app

from codetv.news import News
from codetv.obs import Connection


class SegmentType(Enum):
    VIDEO = "video"
    UP_NEXT = "up-next"


@dataclass
class Segment:
    duration: timedelta
    name: str
    type: SegmentType
    link: Optional[str] = None
    file: Optional[str] = None
    tags: List[str] = field(default_factory=list)


def get_segments() -> List[Segment]:
    with open("schedule.yml", "r") as stream:
        try:
            segments_data: List[Dict] = yaml.safe_load(stream)["segments"]
        except yaml.YAMLError as exc:
            print(exc)

    segments: List[Segment] = []
    for data in segments_data:
        segments.append(
            Segment(
                duration=timedelta(seconds=int(data["duration"][:-1])),
                name=data.get("name"),
                type=SegmentType(data["type"].lower()),
                file=data.get("file"),
                link=data.get("link"),
                tags=data.get("tags", []),
            )
        )
    return segments


class StatefulCircularList(list):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._idx = 0

    def __iter__(self) -> Iterator:
        class Iter:
            def __init__(itr_self):
                itr_self.started = False

            def __iter__(itr_self):
                return itr_self

            def __next__(itr_self):
                if not itr_self.started:
                    val = self.current
                    itr_self.started = True
                else:
                    val = self.next()

                return val

        return Iter()

    def peek_next_iter(self) -> Iterator:
        next_idx = self._find_next_idx()

        return iter(self[next_idx:] + (self[0:next_idx] if next_idx != 0 else []))

    def _find_next_idx(self):
        next_idx = self._idx + 1
        if next_idx == len(self):
            next_idx = 0
        return next_idx

    def _find_prev_idx(self):
        prev_idx = self._idx - 1
        if prev_idx < 0:
            prev_idx = len(self) - 1
        return prev_idx

    @property
    def pos(self) -> int:
        return self._idx

    @property
    def current(self) -> Any:
        return self[self._idx]

    def next(self) -> Any:
        self._idx = self._find_next_idx()
        return self.current

    @property
    def peek_next(self) -> Any:
        return self[self._find_next_idx()]

    @property
    def peek_prev(self) -> Any:
        return self[self._find_prev_idx()]


class Scheduler:
    def __init__(self):
        self.obs: Connection = current_app.obs
        self.video_scene_names = StatefulCircularList(["Video 1", "Video 2"])
        self.video_source_names = StatefulCircularList(
            ["Media: current", "Media: on-deck"]
        )

        self.segments = StatefulCircularList(get_segments())

    async def run(self):
        self.set_next_video()
        for segment in self.segments:
            duration = segment.duration.total_seconds()
            if segment.type == SegmentType.VIDEO:
                self.show_next_video()
                # pause to let the transition play out
                await asyncio.sleep(2)
                duration -= 2
                self.set_next_video()
            elif segment.type == SegmentType.UP_NEXT:
                self.obs.show_scene("Up Next")

            await asyncio.sleep(duration)

    def set_next_video(self):
        next_segment: Segment = next(
            filter(
                lambda item: item.type == SegmentType.VIDEO,
                self.segments.peek_next_iter(),
            ),
            None,
        )
        if next_segment:
            abspath = os.path.abspath(next_segment.file)

            next_source_name = self.video_source_names.current
            print(f"making video {next_segment.name} up next on {next_source_name}")
            self.obs.set_video(next_source_name, abspath)
            self.obs.set_up_next(next_segment.name)
            headlines = []
            if next_segment.tags:
                news: News = current_app.news
                for tag in next_segment.tags:
                    if tag in news.headlines:
                        headlines.extend(news.headlines[tag])

            if headlines:
                random.shuffle(headlines)

            self.obs.set_news_ticker(headlines)

    def show_next_video(self):
        self.obs.show_scene(self.video_scene_names.current)
        self.video_scene_names.next()
        self.video_source_names.next()
        self.obs.set_credits(self.segments.peek_prev.link or "")

        async def credits():
            await asyncio.sleep(3)
            self.obs.toggle_credits(self.video_scene_names.current, True)
            await asyncio.sleep(5)
            self.obs.toggle_credits(self.video_scene_names.current, False)

        asyncio.create_task(credits())
