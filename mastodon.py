# NOTE: scraping is based on the following article: https://james.ashford.phd/2023/02/13/how-to-scrape-mastodon-timelines-using-python-and-pandas/

import requests
from loguru import logger
from bs4 import BeautifulSoup 
from tqdm import tqdm
from datetime import timezone, datetime

from source import Source, Group, Row

SERVERS_AND_USERS : dict[str, list[str]] = {
    "cyberplace.social": [
        "@GossiTheDog",
    ],
    "infosec.exchange": [
        "@jimmychappell",
        "@sirdarckcat",
        "@_marklech_",
        "@maldr0id",
        "@tomchop",
        "@hackndo",
        "@imlordofthering",
        "@sphynx",
        "@trailofbits",
    ],
    "mas.to": [
        "@secwolf404",
    ],
    "fosstodon.org": [
        "@atoponce"
    ],
}

ACCOUNTS_LOOKUP_URL = "https://{server}/api/v1/accounts/lookup"
USER_TOOTS_URL = "https://{server}/api/v1/accounts/{user_id}/statuses"
TOOT_URL = "https://{server}/{user}/{toot_id}"

def _create_time_filter():
    now = datetime.now(timezone.utc)
    def _time_filter(date: str) -> bool:
        dt = datetime.fromisoformat(date)
        return abs((now - dt).days) < 5
    return _time_filter
    
def find_user_id(server: str, user: str) -> str:
    resp = requests.get(ACCOUNTS_LOOKUP_URL.format(server=server), params={"acct": user})
    if resp.status_code != 200:
        logger.error(f"Failed getting user's ID with error {resp.status_code}")
        return ""

    obj : dict = resp.json()
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
    accounts = []
    _time_filter = _create_time_filter()
    for server, users in tqdm(SERVERS_AND_USERS.items(), desc="Mastodon"):
        for user in users:
            account = Group(name=f"{user}@{server}")
            for toot in list_user_toots(server, user):
                if not _time_filter(toot[1]):
                    break
                account.rows.append(Row(
                    title=toot[0],
                    date=toot[1],
                    url=toot[2],
                ))
            if len(account.rows):
                accounts.append(account)
    return Source(name="Mastodon", groups=accounts)
