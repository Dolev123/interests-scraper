#!/usr/bin/env python3
import psycopg
from datetime import datetime
import uuid

from .logs import INFO, WARN, ERROR, DEBUG
from .scrape_model import Scrape

# Report generation

PREPARED_ORDERED_REPORT = """
PREPARE generate_report(timestamp) AS
	SELECT s.type, s.name, sc.title, sc.link, sc.published
	FROM scrapes sc
	JOIN sources s ON s.id = sc.source_id
	WHERE $1 + INTERVAL '1 days' >= sc.published AND $1 - sc.published < INTERVAL '5 days' AND (
		(type = 'rss' AND $1 - sc.published < INTERVAL '2 days') OR
		(type = 'youtube') OR
		(type = 'mastodon')
	)
	ORDER BY sc.published DESC
;
"""
EXECUTE_ORDERED_REPORT = "EXECUTE generate_report('{timestamp}')"

PREPARED_EXPORT_SOURCES = [ """
PREPARE export_rss_sources(int) AS
	SELECT s.id AS uuid, s.name AS name, sr.feed_url as feed_url
	FROM sources s
	JOIN sources_rss sr ON s.id = sr.id
	WHERE s.type = 'rss'
;
""", """
PREPARE export_youtube_sources(int) AS
	SELECT s.id AS uuid, s.name AS channel_name, sy.channel_id as channel_id
	FROM sources s
	JOIN sources_youtube sy ON s.id = sy.id
	WHERE s.type = 'youtube'
;
""", """
PREPARE export_mastodon_sources(int) AS
	SELECT s.id AS uuid, s.name AS user_name, sm.server as server
	FROM sources s
	JOIN sources_mastodon sm ON s.id = sm.id
	WHERE s.type = 'mastodon'
;
"""
]
EXECUTE_EXPORT_SOURCES = {
	"rss": "EXECUTE export_rss_sources(1);",
	"mastodon": "EXECUTE export_mastodon_sources(1);",
	"youtube": "EXECUTE export_youtube_sources(1);",
}
EXECUTE_INSERT_SCRAPE = "SELECT insert_scrape(%s, %s, %s, %s)"

class DBConn:
	def __init__(self, host:str, db:str, user:str, password:str=""):
		self.role = "write" if "write" in user.lower() else "read"
		conn_string = f"host={host} dbname={db} user={user}"
		if password:
			conn_string += f" password='{password}'"
		DEBUG("[DBConn][__init__]", "Initiating DB connection:", conn_string)
		try:
			self.conn = psycopg.connect(conn_string)
			INFO("[DBConn][__init__]", "connected to DB")
		except Exception as e:
			ERROR("[DBConn][__init__]", "failed connecting to DB:", e)

	def commit(self):
		INFO("[DBConn][commit]", "Commiting to DB")
		self.conn.commit()

	def disconnect(self):
		self.conn.close()

	def prepare_session(self):
		try:
			if self.role == "read":
				_ = self.conn.execute(PREPARED_ORDERED_REPORT)
			else:
				for statement in PREPARED_EXPORT_SOURCES:
					self.conn.execute(statement)
		except Exception as e:
			ERROR("[DBConn][prepare_session]", e)
			self.conn.rollback()

	def generate_report(self, when:datetime=None) -> list[tuple]:
		if self.role != "read":
			WARN("[DBConn][generate_report]", "trying to generate report with non 'read' role")
			return
		if not when:
			when = datetime.now()
		try:
			cur = self.conn.execute(EXECUTE_ORDERED_REPORT.format(timestamp=when))
			# TODO: change output to insert into model?/source?
			return cur.fetchall()
		except Exception as e:
			ERROR("[DBConn][generate_report] failed to execute DB statement:", e)
			self.conn.rollback()

	def export_sources(self) -> dict[str, list]:
		if self.role != "write":
			WARN("[DBConn][export_sources]", "trying to export sources with non 'write' role")
			return
		sources = {}
		try:
			for src, statement in EXECUTE_EXPORT_SOURCES.items():
				cur = self.conn.execute(statement)
				sources[src] = cur.fetchall()
			return sources
		except Exception as e:
			ERROR("[DBConn][generate_report] failed to execute DB statement:", e)
			self.conn.rollback()

	def export_sources_list(self) -> list[tuple[str, list]]:
		if self.role != "write":
			WARN("[DBConn][export_sources]", "trying to export sources with non 'write' role")
			return
		sources = []
		try:
			for src, statement in EXECUTE_EXPORT_SOURCES.items():
				cur = self.conn.execute(statement)
				sources += [ (src, x) for x in cur.fetchall() ]
			return sources
		except Exception as e:
			ERROR("[DBConn][generate_report] failed to execute DB statement:", e)
			self.conn.rollback()		

	# def insert_scrape(self, title:str, link:str, published:datetime, source_id:uuid.UUID):
	def insert_scrape(self, scrape:Scrape):
		if self.role != "write":
			WARN("[DBConn][insert_scrape]", "trying to insert scrape with non 'write' role")
			return
		try:
			DEBUG("[DBConn][insert_scrape]", "Inserting a new scrape")
			cur = self.conn.execute(EXECUTE_INSERT_SCRAPE, (scrape.title, scrape.link, scrape.published.replace(tzinfo=None), scrape.source_id,))
			scrape_id = cur.fetchall()
			if len(scrape_id) > 0 and len(scrape_id[0]) > 0 and scrape_id[0][0] is not None:
				INFO("[DBConn][insert_scrape]", "New scrape id:", scrape_id[0][0], "[", scrape.link, "]")
		except Exception as e:
			ERROR("[DBConn][insert_scrape] failed to execute DB statement:", e)

if __name__ == '__main__':
	db = DBConn(os.environ["PSQL_HOST"], os.environ["PSQL_DB"], os.environ["PSQL_USER"], os.environ["PSQL_PASS"])
	db.prepare_session()

	sources = db.export_sources()
	for src, l in sources.items():
		print("----------------\n", src, "\n----------------")
		for o in l:
			print(o)
			
	db.disconnect()
