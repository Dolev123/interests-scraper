-- ### DB Users Setup ### --
CREATE DATABASE scraper;
-- u_writer
CREATE ROLE u_writer LOGIN PASSWORD 'CHANGEME';
GRANT CONNECT ON DATABASE scraper  TO u_writer;
-- u_reader
CREATE ROLE u_reader LOGIN PASSWORD 'CHANGEME';
GRANT CONNECT ON DATABASE scraper TO u_reader;
\c scraper 
-- u_writer permissions
GRANT USAGE ON SCHEMA public TO u_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO u_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO u_writer;
-- u_reader permissions
GRANT USAGE ON SCHEMA public TO u_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO u_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO u_reader;

-- ### DB Structure Setup ### --

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE source_type AS ENUM (
	'rss',
	'youtube',
	'mastodon'
);

CREATE TABLE sources (
	id				UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	name			varchar(64) NOT NULL,
	type			source_type NOT NULL DEFAULT 'rss'
--	Maybe add description (used currently for rss feeds)
--	description		varchar(128) NOT NULL,
);

CREATE TABLE sources_rss (
	id UUID 		references sources(id),
	feed_url 		varchar(128) NOT NULL UNIQUE
);
CREATE TABLE sources_youtube (
	id UUID 		references sources(id),
	channel_id 		varchar(32) NOT NULL UNIQUE
);
CREATE TABLE sources_mastodon (
	id UUID 		references sources(id),
	server 			varchar(64) NOT NULL -- multiple users per serevr -> not UNIQUE
);

CREATE TABLE scrapes (
	id				UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	title 			varchar(256) NOT NULL,
	link 			varchar(256) NOT NULL,
	published 		timestamp NOT NULL,
	source_id 		UUID references sources(id)
);
-- the same source should not have the same title twice (might be problematic with scrapes from social media)
ALTER TABLE scrapes ADD CONSTRAINT scrape_source_and_title UNIQUE (title, source_id);

-- ### Prepared Statements ### --
-- the statement are prepared per user session

-- ## Scraping

PREPARE export_rss_sources(int) AS
	SELECT s.id AS uuid, s.name AS name, sr.feed_url as feed_url
	FROM sources s
	JOIN sources_rss sr ON s.id = sr.id
	WHERE s.type = 'rss'
;

PREPARE export_youtube_sources(int) AS
	SELECT s.id AS uuid, s.name AS channel_name, sy.channel_id as channel_id
	FROM sources s
	JOIN sources_youtube sy ON s.id = sy.id
	WHERE s.type = 'youtube'
;

PREPARE export_mastodon_sources(int) AS
	SELECT s.id AS uuid, s.name AS user_name, sm.server as server
	FROM sources s
	JOIN sources_mastodon sm ON s.id = sm.id
	WHERE s.type = 'mastodon'
;

-- ## Report Generation

PREPARE generate_report(timestamp) AS
	SELECT s.type, s.name, sc.title, sc.link, sc.published
	FROM scrapes sc
	JOIN sources s ON s.id = sc.source_id
	WHERE $1 + INTERVAL '1 days' >= sc.published AND $1 - sc.published < INTERVAL '5 days' AND (
		(type = 'rss' AND $1 - sc.published < INTERVAL '2 days') OR
		(type = 'youtube') OR
		(type = 'mastodon')
	)
;

PREPARE generate_ordered_report(timestamp) AS
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

-- ## Inserting new scrape

-- This is a naive approach, mainly for testing
PREPARE insert_scrape(varchar(256), varchar(256), timestamp, UUID) AS
	INSERT INTO scrapes (title, link, published, source_id)
	VALUES ($1, $2, $3, $4)
;

-- Ensure updating of published (maybe should change to be unique on link and source or only link)
CREATE OR REPLACE FUNCTION insert_scrape(title varchar(256), link varchar(256), published timestamp, source_id UUID) RETURNS UUID
	LANGUAGE SQL
	AS $$
	INSERT INTO scrapes (title, link, published, source_id)
	VALUES (title, link, published, source_id)
	ON CONFLICT (title, source_id)
	DO UPDATE
		SET published = EXCLUDED.published
	WHERE EXCLUDED.published > scrapes.published
	RETURNING id
	$$
;

-- ### New Sources Functions ### --
-- NOTE: need to commit after inserting atleast 1 new source

-- ## RSS

CREATE OR REPLACE FUNCTION new_rss_source(name varchar(64), feed_url varchar(128)) RETURNS uuid
	LANGUAGE SQL
	AS $$
	    WITH new_source AS (
	        INSERT INTO sources(name, type) VALUES ($1, 'rss') 
	        RETURNING id
	    )
	    INSERT INTO sources_rss(id, feed_url)
	    SELECT id, $2 FROM new_source
	    RETURNING id;
	$$
;
SELECT new_rss_source("", ""); -- UUID: 

-- ## Youtube

CREATE OR REPLACE FUNCTION new_youtube_source(name varchar(64), channel_id varchar(32)) RETURNS uuid
	LANGUAGE SQL
	AS $$
	    WITH new_source AS (
	        INSERT INTO sources(name, type) VALUES ($1, 'youtube') 
	        RETURNING id
	    )
	    INSERT INTO sources_youtube(id, channel_id)
	    SELECT id, $2 FROM new_source
	    RETURNING id;
	$$
;
SELECT new_youtube_source("", ""); -- UUID: 

-- ## Mastodon

CREATE OR REPLACE FUNCTION new_mastodon_source(name varchar(64), server varchar(64)) RETURNS uuid
	LANGUAGE SQL
	AS $$
	    WITH new_source AS (
	        INSERT INTO sources(name, type) VALUES ($1, 'mastodon') 
	        RETURNING id
	    )
	    INSERT INTO sources_mastodon(id, server)
	    SELECT id, $2 FROM new_source
	    RETURNING id;
	$$
;
SELECT new_mastodon_source("", ""); -- UUID: 