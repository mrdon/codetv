#!venv/bin/python
import os
from datetime import timedelta, datetime, timezone
from typing import Dict, List

import readchar as readchar
import yaml
from yaml import Loader
from youtube import API

from dotenv import load_dotenv

load_dotenv(".secrets")


api = API(None, None, api_key=os.getenv("YOUTUBE_API_KEY"))
MAX_VIDEOS = 50

for keyword in ("python", "java", "devops", "continuous deployment", "continuous delivery", "rust"):

    print(f"Fetch {keyword} videos? [Y/n]")
    c = readchar.readchar()
    if c != '\r' and c.upper() != 'Y':
        print(f'Skipping {keyword}')
        continue

    output_file = f"videos-{keyword}.yml"
    ignored_videos = []
    loaded_videos = []
    videos: List[Dict] = []
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            data = yaml.load(f, Loader=Loader)
            ignored_videos.extend(data.get("ignored", []))
            loaded_videos.extend((v["url"] for v in data["videos"]))
            videos.extend((v for v in data["videos"]))

    print(f"Found {len(ignored_videos)} ignored videos")
    print(f"Found {len(loaded_videos)} existing videos")

    pages_fetched = 0
    done = False
    while not done or pages_fetched == 10:
        pages_fetched += 1
        pageToken = None
        video_data = api.get('search', q="Python", maxResults=50,
                         videoLicense="creativeCommon", type="video",
                         videoDuration="medium",
                             order="rating",
                         videoDefinition="high",
                         publishedAfter=(datetime.now(timezone.utc) - timedelta(weeks=52 * 4)).isoformat(),
                             pageToken=pageToken)
        pageToken = video_data["nextPageToken"]

        for item in video_data["items"]:
            if len(videos) > MAX_VIDEOS:
                done = True
                break

            url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            if url in ignored_videos or url in loaded_videos:
                continue

            snippet = item["snippet"]
            title = snippet["title"]
            print(f"New video:\n\tTitle: {title}\n\tURL:   {url}\n\tType 'y' to keep")
            c = readchar.readchar()
            if c == 'q':
                print('quitting')
                done = True
                break
            if c != 'y':
                print("Skipping")
                ignored_videos.append(url)
                continue

            data = {}

            data["title"] = title
            data["url"] = url
            data["description"] = snippet["description"]
            data["thumbnail"] = snippet["thumbnails"]["high"]
            data["channel"] = {"title": snippet["channelTitle"], "id": snippet["channelId"]}
            data["publishTime"] = snippet["publishTime"]
            videos.append(data)
            loaded_videos.append(url)
            print(f"Added {data['title']}")
            with open(output_file, "w") as f:
                yaml.dump(dict(videos=videos, ignored=ignored_videos), f)

    print(f"Created file with {len(videos)} videos: {output_file}")
