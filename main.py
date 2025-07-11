import jinja2

from source import Source
import youtube
import mastodon
import rssfeed

def create_report(sources: list[Source]):
    enviroment = jinja2.Environment(loader=jinja2.FileSystemLoader("./"))
    template = enviroment.get_template("results.html.tpl")
    content = template.render(
        sources=sources,
    )

    with open("report.html", "w", encoding="utf-8") as f:
        _ = f.write(content)
        print("Written Report!")

def main():
    sources = [
        youtube.list_videos(),
        mastodon.list_toots(),
        rssfeed.list_feeds(),
    ]
    create_report(sources)

if __name__ == '__main__':
    main()
