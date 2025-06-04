# NOTE: scraping is based on the following article: https://james.ashford.phd/2023/02/13/how-to-scrape-mastodon-timelines-using-python-and-pandas/

import requests
import json
from loguru import logger
from bs4 import BeautifulSoup 
from tqdm import tqdm

from source import Source, Group, Row

SERVERS_AND_USERS = {
    "cyberplace.social": [
        "@GossiTheDog",
    ],
}

ACCOUNTS_LOOKUP_URL = "https://{server}/api/v1/accounts/lookup"
USER_TOOTS_URL = "https://{server}/api/v1/accounts/{user_id}/statuses"
TOOT_URL = "https://{server}/{user}/{toot_id}"

def find_user_id(server: str, user: str) -> str:
    resp = requests.get(ACCOUNTS_LOOKUP_URL.format(server=server), params={"acct": user})
    if resp.status_code != 200:
        logger.error(f"Failed getting user's ID with error {resp.status_code}")
        # from IPython.terminal.embed import embed; embed()
        return ""

    obj = resp.json()
    return obj["id"]

def get_toot_data(toot: dict) -> str:
    if toot["content"]:
        data = toot["content"]
        # return data.split("</p>")[0][len("<p>"):]
    elif toot["reblog"]:
        data = toot["reblog"]["content"]
        # return data.split("</p>")[0][len("<p>"):]
    elif toot["media_attachments"]:
        return "-Mystery-Toot-"
    else:
        logger.warning(f"Failed to get toot's data {toot['id']}")
        return ""
    soup = BeautifulSoup(data.split("</p>")[0] + "</p>", features="html.parser")
    return soup.get_text()

def list_user_toots(server: str, user: str) -> list:
    user_id = find_user_id(server, user)
    if not user_id: 
       return []

    resp = requests.get(USER_TOOTS_URL.format(server=server, user_id=user_id), params={"limit": 10})
    if resp.status_code != 200:
        logger.error(f"Failed getting user's toots with error {resp.status_code}")
        return []

    toots = []
    obj = resp.json()
    for toot in obj:
        data = get_toot_data(toot)
        if not data:
            continue
        url = TOOT_URL.format(
            server=server,
            user=user,
            toot_id=toot["id"],
        )
        toots.append((
            data,
            toot["created_at"],
            url,
        ))
    return toots

def list_toots():
    toots = []
    accounts = []
    for server, users in tqdm(SERVERS_AND_USERS.items(), desc="Mastodon"):
        for user in users:
            account = Group(name=f"{user}@{server}")
            for toot in list_user_toots(server, user):
                account.rows.append(Row(
                    title=toot[0],
                    date=toot[1],
                    url=toot[2],
                ))
            accounts.append(account)
    return Source(name="Mastodon", groups=accounts)
