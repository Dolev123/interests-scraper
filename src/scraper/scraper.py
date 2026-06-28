#!/usr/bin/env python3
import os
from concurrent.futures import ThreadPoolExecutor
import threading

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
os.sys.path.append(parent_dir_name)

from internal.db import DBConn
from internal.logs import INFO, WARN, ERROR, DEBUG
from internal.scrape_model import Scrape

from mastodon import MastodonSource
from rssfeed import RSSSource
from youtube import YoutubeSource

VIDEOS_LIST_URL="https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

ACCOUNTS_LOOKUP_URL = "https://{server}/api/v1/accounts/lookup"
USER_TOOTS_URL = "https://{server}/api/v1/accounts/{user_id}/statuses"
TOOT_URL = "https://{server}/{user}/{toot_id}"

WORKERS_COUNT = 10

g_db_lock = threading.Lock()
g_db: DBConn = None

def initiate_db_connection():
	global g_db
	INFO("[initiate_db_connection]", "Connecting to DB")
	try:
		g_db = DBConn(os.environ["PSQL_HOST"], os.environ["PSQL_DB"], os.environ["PSQL_USER"], os.environ["PSQL_PASS"])
		g_db.prepare_session()
	except Exception as e:
		ERROR("[initiate_db_connection]", e)
		os.sys.exit(1)

def handle_source(raw_source: tuple, src_type: str):
	scrapes: list[Scrape] = []
	try:
		INFO("[handle_source]", "Handling source:", raw_source[0])
		match src_type:
			case "rss":
				r = RSSSource(source_id=raw_source[0], title=raw_source[1], feed_url=raw_source[2])
				scrapes = r.parse_feed()
			case "youtube":
				y = YoutubeSource(source_id=raw_source[0], channel_name=raw_source[1], channel_id=raw_source[2])
				scrapes = y.list_videos()
			case "mastodon":
				m = MastodonSource(source_id=raw_source[0], username=raw_source[1], server=raw_source[2])
				m.update_user_id()
				scrapes = m.list_user_toots()
			case _:
				ERROR("[handle_source]", "Unknown source type:", src_type)
				return
	except Exception as e:
		ERROR("[handle_source]", "Error:", e)

	DEBUG("[handle_source]", "len(scrapes):", len(scrapes))
	if len(scrapes) > 0:
		with g_db_lock:
			for scrape in scrapes:
				g_db.insert_scrape(scrape)

def dispatch_scraping(sources: list[tuple[str, list]]):
	INFO("[dispatch_scraping]", f"Dispatching {len(sources)} sources over {WORKERS_COUNT} workers")
	with ThreadPoolExecutor(max_workers=WORKERS_COUNT) as executor:
		for source in sources:
			executor.submit(handle_source, source[1], source[0])
	g_db.commit()


if __name__ == '__main__':
	DEBUG("[TEST]", "DEBUG")
	INFO("[TEST]", "INFO")
	WARN("[TEST]", "WARN")
	ERROR("[TEST]", "ERROR")
	initiate_db_connection()
	sources = g_db.export_sources_list()
	dispatch_scraping(sources)

	g_db.disconnect()