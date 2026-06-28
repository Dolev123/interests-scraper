#!/usr/bin/env python3

from pydantic import BaseModel
from uuid import UUID
import feedparser
from datetime import datetime, timezone
from time import mktime

import os
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
os.sys.path.append(parent_dir_name)

from internal.scrape_model import Scrape
from internal.logs import INFO, WARN, ERROR, DEBUG

class RSSSource(BaseModel):
	source_id: UUID
	title: str
	feed_url: str

	def parse_feed(self, days_delta:int=1) -> list[Scrape]:
		try:
			DEBUG("[RSSSource][parse_feed]", "Parsing feed:", self.feed_url)
			parsed = feedparser.parse(self.feed_url)
			# TODO:: maybe add support for subtitle, requires changes to all
			# title = parsed.feed.get("title", feed_url.split("/")[2])
			# subtitle = parsed.feed.get('subtitle', '')
			
			if len(parsed.entries) == 0:
				WARN("[RSSSource][parse_feed]", "No entries for feed:", self.title)
			entries = []
			for entry in parsed.entries:
				# check if entry updated
				recent_time = entry.updated_parsed if entry.get("updated_parsed") else entry.published_parsed
				recent_time = datetime.fromtimestamp(mktime(recent_time))
				if abs((recent_time - datetime.now()).days) > days_delta:
					DEBUG("[RSSSource][parse_feed]", "Feed entry too old:", entry.link)
					continue
				entries.append(Scrape(
					title=str(entry.title),
					link=str(entry.link),
					published=recent_time,
					source_id=self.source_id,
				))
				DEBUG("[RSSSource][parse_feed]", "Scraped new rss entry:", entries[-1])
			return entries
		except Exception as e:
			ERROR("[RSSSource][parse_feed]", "Encountered an error:", e)
			return None

