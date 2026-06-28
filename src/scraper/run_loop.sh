#!/bin/sh

source scraper-env/bin/activate

TIMER=${TIMER:=2h}

while :
do
	echo '[+] Scraping'
	python3 scraper/scraper.py
	echo '[+] Sleeping for $TIMER'
	sleep $TIMER
done
