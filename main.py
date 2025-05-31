import jinja2

import youtube
import mastodon

def create_report(sources: list):
    enviroment = jinja2.Environment(loader=jinja2.FileSystemLoader("./"))
    template = enviroment.get_template("results.html.tpl")
    content = template.render(
        sources=sources,
    )

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(content)
        print("Written Report!")

def main():
    sources = [
        youtube.list_videos(),
        mastodon.list_toots(),
    ]
    create_report(sources)

if __name__ == '__main__':
    main()
