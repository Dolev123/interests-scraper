from pydantic import BaseModel

class Row(BaseModel):
    title: str
    date: str
    url: str

class Group(BaseModel):
    name: str
    rows: list[Row] = []

class Source(BaseModel):
    name: str
    groups: list[Group]
