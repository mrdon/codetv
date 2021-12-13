from collections import defaultdict
from typing import Dict
from typing import List

import aiohttp
import feedparser
from feedparser import FeedParserDict


class News:
    def __init__(self):
        self.headlines: Dict[str, List[str]] = defaultdict(list)

    async def load(self):
        async with aiohttp.ClientSession() as session:
            for topic in ("python", "java"):
                async with session.get(
                    f"https://www.infoworld.com/category/{topic}/index.rss"
                ) as response:
                    if response.status == 200:
                        body = await response.text()
                        feed: FeedParserDict = feedparser.parse(body)
                        for entry in feed.entries:
                            self.headlines[topic].append(entry.title)
                        print(
                            f"Loaded {len(self.headlines[topic])} titles for topic {topic}"
                        )
