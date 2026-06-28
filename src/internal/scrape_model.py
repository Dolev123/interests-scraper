#!/usr/bin/env python3
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class Scrape(BaseModel):
	title: str
	link: str
	published: datetime
	source_id: UUID

