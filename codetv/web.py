# noinspection PyUnresolvedReferences
import asyncio
import logging
import os
from datetime import timedelta
from typing import List

from quart import current_app
from quart import Quart
from quart import render_template

from codetv import obs
from codetv.news import News
from codetv.schedule import Scheduler
from codetv.schedule import Segment
from codetv.schedule import SegmentType

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


app = Quart(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "not-so-secret")

app.config["QUART_AUTH_COOKIE_SECURE"] = False
app.config["env"] = "development"
app.config["QUART_DEBUG"] = True
app.config["DEBUG"] = True
app.secret_key = os.environ.get("SECRET_KEY", "not-so-secret")

logging.basicConfig()
log = logging.getLogger(__name__)


@app.before_serving
async def start_bot():
    current_app.obs = obs.Connection()
    scheduler = Scheduler()
    current_app.scheduler = scheduler
    asyncio.create_task(scheduler.run())
    news = News()
    asyncio.create_task(news.load())
    current_app.news = news
    print("started")


@app.route("/health", methods=["GET"])
async def health():
    return "UP", 200


@app.route("/", methods=["GET"])
async def get_slide_index():
    return "UP", 200


@app.route("/up-next", methods=["GET"])
async def get_up_next():
    now = timedelta(seconds=5)
    next_segments: List[Segment] = []
    next_offsets: List[str] = []
    for segment in current_app.scheduler.segments.peek_next_iter():
        if segment.type == SegmentType.VIDEO:
            next_segments.append(segment)
            minutes = int(now.total_seconds() / 60)
            secs = int(now.total_seconds() % 60)
            if secs:
                next_offsets.append(f"{minutes}:{secs}s")
            else:
                next_offsets.append(f"{minutes}m")
        now += segment.duration
        if len(next_segments) == 5:
            break
    return await render_template(
        f"up_next.html", next_segments=next_segments, next_offsets=next_offsets
    )


@app.route("/video-background", methods=["GET"])
async def get_video_background():
    return await render_template(f"video_background.html")
