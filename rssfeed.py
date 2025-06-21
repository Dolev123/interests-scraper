import feedparser
from tqdm import tqdm
from datetime import datetime
from time import struct_time

from source import Row, Group, Source

FEEDS : list[str] = [
    "https://www.kaspersky.co.uk/blog/feed/",
    "https://blog.cloudflare.com/rss/",
    "https://hackaday.com/blog/feed/",
    "https://horizon3.ai/category/attack-research/attack-blogs/feed/",
    "https://www.securityweek.com/feed/",
    "https://www.bleepingcomputer.com/feed/",
    "https://www.cshub.com/rss/reports",
    "https://www.cshub.com/rss/articles",
    "https://www.theregister.com/security/headlines.atom",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.helpnetsecurity.com/feed/",
    "https://www.phoronix.com/rss.php",
    "https://investor.qualys.com/rss/news-releases.xml",
    "https://msrc.microsoft.com/blog/feed",
    "https://msrc.microsoft.com/blog/categories/bluehat/feed",
    "https://msrc.microsoft.com/blog/categories/security-research-defense/feed",
    "https://msrc.microsoft.com/blog/categories/microsoft-threat-hunting/feed",
    "https://www.huntress.com/blog/rss.xml",
    "http://feeds.feedburner.com/eset/blog?format=xml",
    "https://www.bitdefender.com/nuxt/api/en-us/rss/labs/",
    "https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v",
    "https://googleprojectzero.blogspot.com/feeds/posts/default",
    "https://www.zerodayinitiative.com/blog/?format=rss",
    "https://www.zerodayinitiative.com/rss/upcoming/",
    "https://www.zerodayinitiative.com/rss/published/",
    "https://blog.talosintelligence.com/feed/",
    "https://blog.sekoia.io/feed/",
    "https://cybersecurityventures.com/feed/",
    "https://lifeboat.com/blog/category/cybercrime-malcode/feed",
    "https://feeds.feedblitz.com/GDataSecurityBlog-EN&x=1",
    "https://ccgnludelhi.wordpress.com/feed/",
    "https://www.cybertrace.com.au/blog/feed/",
    "https://www.malwarebytes.com/blog/feed/index.xml",
    "https://intel471.com/blog/feed",
]

def _create_time_filter():
    now = datetime.now()
    def _time_filter(date: struct_time) -> bool:
        dt = datetime(date.tm_year, date.tm_mon, date.tm_mday)
        return abs((now - dt).days) < 100
    return _time_filter

def _check_feeds_are_valid():
    for feed_url in FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            print(f"Title: {parsed.feed.title}:")
            for entry in parsed.entries:
                print(f"{entry.title} \t|\t{entry.link}")
        except Exception as e:
            print(f"[!] Failed to parse {feed_url}")
        finally:
            print()

def list_feeds():
    feeds = []
    _time_filter = _create_time_filter()
    for feed_url in tqdm(FEEDS, desc="RSS Feeds"):
        parsed = feedparser.parse(feed_url)
        feed = Group(name=parsed.feed.title)
        for entry in parsed.entries:
            if not _time_filter(entry.published_parsed):
                break
            feed.rows.append(Row(
                title=entry.title,
                date=entry.published,
                url=entry.link
            ))
            if len(feed.rows) >= 10:
                # continue
                break
        if len(feed.rows):
            feeds.append(feed)
    return Source(name="RSS Feeds", groups=feeds)

if __name__ == '__main__':
    _check_feeds_are_valid()
