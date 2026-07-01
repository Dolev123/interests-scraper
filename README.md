# Interests Scraper

A very basic and (now less) low effort scraper for (mostly) cybersecurity related stuff.  

## Architecture

There are 3 parts to the project:
- __Postgresql__ DB - store both sources to scrape and scraped data.
- __Website__ - A python HTTP server to generate report of what was scraped.
- __Scraper__ - A script to go over all sources and scrape them.

Accessing the website will return the report for the current date, unless date specified with the following URL: `http://host/yyyy-mm-dd/`.  

## Usage

There are docker files provided for both `scraper` and `website` parts, and `postgres:14.23-alpine3.24` is recommecnded for the DB image. 
```sh
# Setup DB
sudo docker run -e POSTGRES_PASSWORD=Password1 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:14.23-alpine3.24
psql -U postgres -h $DB_IP -f setup_db.sql
psql -U postgres -h $DB_IP -d scraper -f insert_sources.sql

# Build
cd src
sudo docker build --file WebsiteDockerfile -t website .
sudo docker build --file ScraperDockerfile -t scraper .

# Run, `-t` is required since logging has ANSI colours
sudo docker run -t -d -e PSQL_HOST=$DB_IP -e PSQL_PASS=CHANGEME website
sudo docker run -t -d -e PSQL_HOST=$DB_IP -e PSQL_PASS=CHANGEME scraper

# For running scraper in a loop:
sudo docker run -t -e PSQL_HOST=$DB_IP -e PSQL_PASS=CHANGEME --entrypoint='scraper/run_loop.sh' scraper
```

For installing as a service (using debian/ubuntu with systemd) without a docker:
```sh
# installing scraper service
chmod +x create_scraper_service.sh && sudo ./create_scraper_service.sh
# installing website service
chmod +x create_website_service.sh && sudo ./create_website_service.sh
```
