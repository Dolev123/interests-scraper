#!/bin/sh

export SRV_DIR=/tmp/srv

function check_srv_dir() {
    if [ ! -d "$SRV_DIR" ]; then
	echo "[+] Creating server directory '$SRV_DIR'"
	mkdir $SRV_DIR
    fi
}

function start_http_server() {
    check_srv_dir
    cd $SRV_DIR
    echo "[+] Starting Server"
    ip a
    python -m http.server 8080 &
}

function update_report() {
    while :
    do
	echo "[+] Updateiong Report"
	check_srv_dir
	cd $WORK_DIR
	. bin/activate
	python main.py
	[[ -e report.html ]] && cp report.html "$SRV_DIR/$(date +%Y-%m-%d).html" || echo "[!] Could not generate report."
	sleep 2h
    done
}

start_http_server
update_report
