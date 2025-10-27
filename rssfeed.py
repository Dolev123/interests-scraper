from re import sub
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
    "https://newsroom.trendmicro.com/cyberthreat?pagetemplate=rss",
    "https://newsroom.trendmicro.com/education?pagetemplate=rss",
    "https://newsroom.trendmicro.com/news-releases?pagetemplate=rss&category=787",
    "https://www.reversinglabs.com/blog/rss.xml",
    "https://checkmarx.com/feed/?post_type=zero-post",
    "https://checkmarx.com/feed/",
    "https://citizenlab.ca/category/research/feed",
    "https://citizenlab.ca/feed",
    "https://cloudblog.withgoogle.com/rss/",
    "https://blog.google/rss/",
    "https://zimperium.com/blog/rss.xml",
    "https://promon.io/security-news/rss.xml",
    "https://cyble.com/blog/feed/",
    "https://www.securonix.com/blog/feed/",
    "https://securityscorecard.com/blog/feed/",
    "https://securityscorecard.com/resources/research/feed",
    "https://blog.sekoia.io/feed",
    "https://blog.trailofbits.com/index.xml",
    "https://blog.redteam-pentesting.de/posts/index.xml",
    "https://talkback.sh/resources/feed/",
    "https://00f.net/atom.xml",
    # TODO:: make a seperate source, because they don't have timestamps
    # "https://bughunters.google.com/feed/en", 
    "https://defensescoop.com/feed/",
    "https://blog.nns.ee/index.xml",
    "https://norvig.com/rss-feed.xml",
    "https://margin.re/blog/rss/",
    "https://cocomelonc.github.io/feed.xml",
    "https://thorstenball.com/atom.xml",
    "https://blog.apnic.net/feed/",
    "https://specterops.io/blog/category/research/feed/",
    "https://labs.watchtowr.com/feed/",
    "https://rss.app/feeds/Ho4gIVhEXQwiIoOx.xml",
]

def _create_time_filter():
    now = datetime.now()
    def _time_filter(date: struct_time) -> bool:
        dt = datetime(date.tm_year, date.tm_mon, date.tm_mday)
        return abs((now - dt).days) < 2
    return _time_filter

def _check_feeds_are_valid():
    for feed_url in FEEDS:
        if not feed_url.startswith("https://"):
            print(f"[!] Warning, feed url does not start with 'https://' : {feed_url}\n")
            continue
        try:
            parsed = feedparser.parse(feed_url)
            title = parsed.feed.get("title", feed_url.split("/")[2])
            print(f"## Title: {title} ##")
            for entry in parsed.entries:
                print(f"{entry.title} \t|\t{entry.link}")
        except Exception as e:
            print(f"[!] Failed to parse {feed_url}")
            print(f"\t[!] Error: {e}")
        finally:
            print()

def list_feeds():
    feeds = []
    _time_filter = _create_time_filter()

    for feed_url in tqdm(FEEDS, desc="RSS Feeds"):
        parsed = feedparser.parse(feed_url)
        title = parsed.feed.get("title", feed_url.split("/")[2])
        subtitle = parsed.feed.get('subtitle', '')
        if len(subtitle) > 80 or subtitle == title:
            subtitle = feed_url.split("/")[2]
        feed = Group(name=title, desc=subtitle)
        for entry in parsed.entries:
            entry_time = entry.get("published_parsed") or entry.get("updated_parsed")
            if not _time_filter(entry_time):
                break
            feed.rows.append(Row(
                title=entry.title,
                date=entry.published,
                url=entry.link
            ))
            if len(feed.rows) >= 10:
                break
        if len(feed.rows):
            feeds.append(feed)
    return Source(name="RSS Feeds", groups=feeds)

if __name__ == '__main__':
    _check_feeds_are_valid()
