import requests
import xmltodict
from tqdm import tqdm
from loguru import logger
from datetime import timezone, datetime

from source import Row, Group, Source

CHANNELS : dict[str,str] = {
    "John Hammond": "UCVeW9qkBjo3zosnqUbG7CFw",
    "Low Level": "UC6biysICWOJ-C3P4Tyeggzg",
    "Live Overflow": "UClcE-kVhqyiHCcjYwcpfj9w",
    "Off By One Security": "UCc8gr33-DyCZ6gAmqdcyzgA",
    "PC Security": "UCKGe7fZ_S788Jaspxg-_5Sg",
    "IppSec": "UCa6eh7gCkpPo5XXUDfygQQA",
    "NahamSec": "UCCZDt7MuC3Hzs6IH4xODLBw",
    "Nir Lichtman": "UCAMu6Dso0ENoNm3sKpQsy0g",
    "Security Weekly - A CRA Resource": "UCg--XBjJ50a9tUhTKXVPiqg",
}

VIDEOS_LIST_URL="https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

def _create_time_filter():
    now = datetime.now(timezone.utc)
    def _time_filter(date: str) -> bool:
        dt = datetime.fromisoformat(date)
        return abs((now - dt).days) < 5
    return _time_filter

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
        if len(videos) >= 10:
            break
    return videos

def list_videos():
    """
    Scrape videos of channels stored at CHANNELS, and retrurn them as Source.
    """
    channels = []
    _time_filter = _create_time_filter()
    for name, cid in tqdm(CHANNELS.items(), desc="YouTube"):
        channel = Group(name=name)
        for video in list_channel_videos(cid):
            if not _time_filter(video[1]):
                break
            channel.rows.append(Row(
                title=video[0],
                date=video[1],
                url=video[2],
            ))
        if len(channel.rows):
            channels.append(channel)
        # print()
    return Source(name="YouTube", groups=channels)
