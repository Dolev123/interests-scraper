#!/usr/bin/env python3

from pydantic import BaseModel
from uuid import UUID
import feedparser
from datetime import timezone, datetime
from time import mktime

import os
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
os.sys.path.append(parent_dir_name)

from internal.scrape_model import Scrape
from internal.logs import INFO, WARN, ERROR, DEBUG

VIDEOS_LIST_URL="https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

class YoutubeSource(BaseModel):
	source_id: UUID
	channel_name: str
	channel_id: str

	@property
	def videos_list_url(self) -> str:
		return VIDEOS_LIST_URL.format(channel_id=self.channel_id)

	def list_videos(self, days_delta:int=1) -> list[Scrape]:
		try:
			DEBUG("[YoutubeSource][list_videos]", "Parsing youtube channel:", self.channel_name)
			parsed = feedparser.parse(self.videos_list_url)
			# TODO:: maybe add support for subtitle, requires changes to all
			# title = parsed.feed.get("title", feed_url.split("/")[2])
			# subtitle = parsed.feed.get('subtitle', '')
			
			if len(parsed.entries) == 0:
				WARN("[YoutubeSource][list_videos]", "No videos for channel:", self.channel_name)
				return
			entries = []
			for entry in parsed.entries:
				# check if entry updated
				recent_time = entry.updated_parsed if entry.get("updated_parsed") else entry.published_parsed
				recent_time = datetime.fromtimestamp(mktime(recent_time))
				if abs((recent_time - datetime.now()).days) > days_delta:
					DEBUG("[YoutubeSource][list_videos]", "Youtube video too old:", entry.link)
					continue
				entries.append(Scrape(
					title=entry.title,
					link=entry.link,
					published=recent_time,
					source_id=self.source_id,
				))
				DEBUG("[YoutubeSource][list_videos]", "Scraped new youtube video:", entries[-1])
			return entries
		except Exception as e:
			ERROR("[YoutubeSource][list_videos]", "Encountered an error:", e)
			raise e
			return None