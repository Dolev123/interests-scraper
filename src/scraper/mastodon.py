#!/usr/bin/env python3
# NOTE: scraping is based on the following article: https://james.ashford.phd/2023/02/13/how-to-scrape-mastodon-timelines-using-python-and-pandas/

from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import timezone, datetime
import requests
from bs4 import BeautifulSoup 

import os
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
os.sys.path.append(parent_dir_name)

from internal.scrape_model import Scrape
from internal.logs import ERROR, WARN, INFO, DEBUG

TOOTS_LIMIT = 10
ACCOUNTS_LOOKUP_URL = "https://{server}/api/v1/accounts/lookup"
USER_TOOTS_URL = "https://{server}/api/v1/accounts/{user_id}/statuses"
TOOT_URL = "https://{server}/{user}/{toot_id}"

class MastodonSource(BaseModel):
	source_id: UUID
	username: str
	server: str
	user_id: Optional[str] = ""

	@property
	def account_lookup_url(self):
		return ACCOUNTS_LOOKUP_URL.format(server=self.server)
	@property
	def user_toots_url(self):
		return USER_TOOTS_URL.format(server=self.server, user_id=self.user_id)

	def update_user_id(self):
		resp = requests.get(self.account_lookup_url, params={"acct": "@"+self.username})
		if resp.status_code != 200:
			ERROR("[MastodonSource][update_user_id]", "Failed getting user's ID with error:", resp.status_code)
			return ""
		obj : dict = resp.json()
		self.user_id = obj["id"]
		DEBUG("[MastodonSource][update_user_id]", f"extracted user id for {self.username}:", self.user_id)

	@staticmethod
	def _parse_toot_data(toot: dict) -> str:
		if toot["content"]:
			data = toot["content"]
		elif toot["reblog"]:
			data = toot["reblog"]["content"]
		elif toot["media_attachments"]:
			return f"-Mystery-Toot-[{toot['id']}]-"
		else:
			WARN["[MastodonSource][_parse_toot_data]", f"Failed to get toot's data {toot['id']}"]
			return ""
		soup = BeautifulSoup(data.split("</p>")[0] + "</p>", features="html.parser")
		return soup.get_text()

	def list_user_toots(self, limit:int=TOOTS_LIMIT, days_delta:int=1) -> list[Scrape]:
		resp = requests.get(self.user_toots_url, params={"limit": limit})
		if resp.status_code != 200:
			ERROR("[MastodonSource][list_user_toots]", "Failed getting user's toots with error:", resp.status_code)
			return []

		obj = resp.json()
		DEBUG("[MastodonSource][list_user_toots]", f"Listed {len(obj)} toots from {self.username}")
		toots: list[Scrape] = []
		for toot in obj:
			data = MastodonSource._parse_toot_data(toot)
			if not data:
				WARN("[MastodonSource][list_user_toots]", "No data for toot:", toot["url"])
				continue
			created = datetime.fromisoformat(toot["created_at"])
			if abs((created - datetime.now(timezone.utc)).days) > days_delta:
				DEBUG("[MastodonSource][list_user_toots]", "Toot too old:", toot["url"])
				continue

			toots.append(Scrape(
				title=str(data),
				link=str(toot["url"]),
				published=created,
				source_id=self.source_id,
			))
			DEBUG("[MastodonSource][list_user_toots]", "Scraped new toot:", toots[-1])
		return toots
