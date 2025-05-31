import requests
import xmltodict
from loguru import logger

from source import Row, Group, Source

CHANNELS = {
    "John Hammond": "UCVeW9qkBjo3zosnqUbG7CFw",
    "Low Level": "UC6biysICWOJ-C3P4Tyeggzg",
    "Live Overflow": "UClcE-kVhqyiHCcjYwcpfj9w",
}

VIDEOS_LIST_URL="https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

def list_channel_videos(channel_id: str) -> list:
    resp = requests.get(VIDEOS_LIST_URL.format(channel_id=channel_id))                 
    if resp.status_code != 200:
        logger.error(f"Failed getting videos list with error {resp.status_code}")
        return []
    
    obj = xmltodict.parse(resp.text)
    entries = obj["feed"]["entry"]
    videos = []
    for entry in entries:
        videos.append((
            entry["title"], 
            entry["published"], 
            entry["media:group"]["media:content"]["@url"],
        ))
        if len(videos) >= 3:
            break
    return videos

def list_videos():
    print("YOUTUBE")
    channels = []
    for name, cid in CHANNELS.items():
        print(f"{name}:")
        channel = Group(name=name)
        for video in list_channel_videos(cid):
            channel.rows.append(Row(
                title=video[0],
                date=video[1],
                url=video[2],
            ))
            print(" | ".join(video))
        channels.append(channel)
        print()
    return Source(name="YouTube", groups=channels)
