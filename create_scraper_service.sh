#!/usr/bin/env bash

SERVICE_DIR=/usr/local/scraper
LOGS_DIR=/var/log/scraper
SCRAPER_DIR="$SERVICE_DIR/interests-scraper/src/scraper"

# Configure postgres connection
if (( $# != 3 )); then
        echo "Usage: $0 <PSQL_HOST> <PSQL_PASS> <TIMER>"
        exit 1
fi
PSQL_HOST="$1"
PSQL_PASS="$2"
TIMER="$3"

# create User if needed
grep -E '^scraper:' /etc/passwd 2>&1 > /dev/null || useradd scraper

# Service files and directories
if [[ ! -d $SERVICE_DIR ]]; then
        echo "[+] Creating service directory"
        mkdir -p $SERVICE_DIR
        echo "[+] Writing $SERVICE_DIR/scraper.service"
        cat > $SERVICE_DIR/scraper.service <<EOF
[Unit]
Description=Cybersecurity news scraper
After=default.target

[Service]
User=scraper
Group=scraper
WorkingDirectory=$SERVICE_DIR
ExecStart=$SERVICE_DIR/run_loop.sh
Type=exec
Restart=always


[Install]
WantedBy=default.target
EOF
        echo "[+] Copying to /etc/systemd/system/scraper.service"
        cp $SERVICE_DIR/scraper.service /etc/systemd/system/scraper.service

        echo "[+] Writing $SERVICE_DIR/run_loop.sh"
        cat > $SERVICE_DIR/run_loop.sh <<EOF
#!/usr/bin/env bash
source $SERVICE_DIR/scraper-env/bin/activate

while :
do
        PSQL_HOST='$PSQL_HOST' PSQL_PASS='$PSQL_PASS' PSQL_DB=scraper PSQL_USER=u_writer python3 $SCRAPER_DIR/scraper.py >> $LOGS_DIR/scraper.log 2>> $LOGS_DIR/scraper_err.log
        echo "[+] Sleeping for $TIMER" >> $LOGS_DIR/scraper.log
        sleep $TIMER
done
EOF
        chmod +x $SERVICE_DIR/run_loop.sh
fi

if [[ ! -d $SERVICE_DIR/interests-scraper ]]; then
        echo "[+] Cloning repository"
        git clone https://github.com/Dolev123/interests-scraper.git $SERVICE_DIR/interests-scraper
fi
if [[ ! -d $SERVICE_DIR/scraper-env ]]; then
        which pip 2>&1 > /dev/null || apt install -y python3-pip python3-venv
        echo "[+] Creating python venv"
        python3 -m venv $SERVICE_DIR/scraper-env
        source $SERVICE_DIR/scraper-env/bin/activate
        pip install -r $SCRAPER_DIR/requirements.txt
fi
chown -R scraper:scraper $SERVICE_DIR

# Logs
if [[ ! -d $LOGS_DIR ]]; then
        echo "[+] Creating log directories"
        mkdir -p $LOGS_DIR
        chown -R scraper:scraper $LOGS_DIR
fi

echo "[+] Reload systemctl"
systemctl daemon-reload
echo "[+] Enable service"
systemctl enable scraper.service
echo "[+] Start service"
systemctl start scraper.service
echo "[+] Status:"
systemctl status scraper.service
