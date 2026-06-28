#!/usr/bin/env python3
import jinja2
import os
from http import HTTPStatus
import http.server
import socketserver
from datetime import datetime
import re

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
os.sys.path.append(parent_dir_name)

from internal.db import DBConn
from internal.logs import INFO, WARN, ERROR, DEBUG


PORT = int(os.environ.get("UI_PORT", 8000))

enviroment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__))))
template = enviroment.get_template("new_report.html.tpl")
g_db: DBConn = None

class ScraperUIHandler(http.server.SimpleHTTPRequestHandler):
	def do_GET(self):
		if self.path.startswith("/favicon.ico"):
			return super().do_GET()
		INFO("[ScraperUIHandler][do_GET]", "request for path:", self.path)
		timestamp = self._check_requested_report_datetime()
		if not timestamp:
			return
		DEBUG("[ScraperUIHandler][do_GET]", "request for datetime:", f"{timestamp.year}-{timestamp.month}-{timestamp.day}" if isinstance(timestamp, datetime) else "None")
		content = self._load_report(timestamp)
		INFO("[ScraperUIHandler][do_GET]", "rendered report")

		self.send_response(HTTPStatus.OK)
		self.send_header("Content-Type", "text/html")
		self.send_header("Content-Length", len(content))
		self.end_headers()
		self.wfile.write(content.encode())

	def _check_requested_report_datetime(self):
		path = self.path.split("?")[0]
		match = re.findall("^/(\\d+-\\d+-\\d+)/", path)
		requested_date = match[0] if len(match) else None
		if "/" == path:
			return datetime.now()
		elif not requested_date:
			INFO("[ScraperUIHandler][_check_requested_report_datetime]", "Redirect to '/'")
			self.send_response(HTTPStatus.FOUND)
			self.send_header("Location", "/")
			self.end_headers()
			return
		elif f"/{requested_date}/" != path:
			INFO("[ScraperUIHandler][_check_requested_report_datetime]", f"Redirect to '/{requested_date}/'")
			self.send_response(HTTPStatus.FOUND)
			self.send_header("Location", f"/{requested_date}/")
			self.end_headers()
			return
		try:
			return datetime.fromisoformat(requested_date)
		except ValueError:
			WARN("[ScraperUIHandler][_check_requested_report_datetime]", "Failed to parse date:", f"'{requested_date}'")
			self.send_response(HTTPStatus.BAD_REQUEST)
			self.end_headers()
			return

	def _load_report(self, timestamp: datetime=None):
		if timestamp:
			report = g_db.generate_report(timestamp)
		else:
			report = g_db.generate_report(datetime.now())
		return template.render(scrapes=report)

def initiate_db_connection():
	global g_db
	INFO("[initiate_db_connection]", "Connecting to DB")
	try:
		g_db = DBConn(os.environ["PSQL_HOST"], os.environ["PSQL_DB"], os.environ["PSQL_USER"], os.environ["PSQL_PASS"])
		g_db.prepare_session()
	except Exception as e:
		ERROR("[initiate_db_connection]", e)
		os.sys.exit(1)

if __name__ == '__main__':
	DEBUG("[TEST]", "DEBUG")
	INFO("[TEST]", "INFO")
	WARN("[TEST]", "WARN")
	ERROR("[TEST]", "ERROR")
	initiate_db_connection()
	with socketserver.TCPServer(("", PORT), ScraperUIHandler) as httpd:
		try:
			httpd.serve_forever()
		except KeyboardInterrupt:
			pass
	g_db.disconnect()