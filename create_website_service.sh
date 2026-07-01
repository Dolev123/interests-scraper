#!/usr/bin/env bash

SERVICE_DIR=/usr/local/website
LOGS_DIR=/var/log/website
WEBSITE_DIR="$SERVICE_DIR/interests-scraper/src/website"

# Configure postgres connection
if (( $# != 2 )); then
        echo "Usage: $0 <PSQL_HOST> <PSQL_PASS>"
        exit 1
fi
PSQL_HOST="$1"
PSQL_PASS="$2"

# create User if needed
grep -E '^website:' /etc/passwd 2>&1 > /dev/null || useradd website

# Service files and directories
if [[ ! -d $SERVICE_DIR ]]; then
        echo "[+] Creating service directory"
        mkdir -p $SERVICE_DIR
        echo "[+] Writing $SERVICE_DIR/website.service"
        cat > $SERVICE_DIR/website.service <<EOF
[Unit]
Description=Cybersecurity news website
After=default.target

[Service]
User=website
Group=website
WorkingDirectory=$SERVICE_DIR
ExecStart=$SERVICE_DIR/run_website.sh
Type=exec
Restart=always


[Install]
WantedBy=default.target
EOF
        echo "[+] Copying to /etc/systemd/system/website.service"
        cp $SERVICE_DIR/website.service /etc/systemd/system/website.service

        echo "[+] Writing $SERVICE_DIR/run_website.sh"
        cat > $SERVICE_DIR/run_website.sh <<EOF
#!/usr/bin/env bash
source $SERVICE_DIR/website-env/bin/activate
PSQL_HOST='$PSQL_HOST' PSQL_PASS='$PSQL_PASS' PSQL_DB=scraper PSQL_USER=u_reader python3 $WEBSITE_DIR/server.py >> $LOGS_DIR/website.log 2>> $LOGS_DIR/website_err.log
EOF
        chmod +x $SERVICE_DIR/run_website.sh
fi

if [[ ! -d $SERVICE_DIR/interests-scraper ]]; then
        echo "[+] Cloning repository"
        git clone https://github.com/Dolev123/interests-scraper.git $SERVICE_DIR/interests-scraper
fi
if [[ ! -d $SERVICE_DIR/website-env ]]; then
        which pip 2>&1 > /dev/null || apt install -y python3-pip python3-venv
        echo "[+] Creating python venv"
        python3 -m venv $SERVICE_DIR/website-env
        source $SERVICE_DIR/website-env/bin/activate
        pip install -r $WEBSITE_DIR/requirements.txt
fi
chown -R website:website $SERVICE_DIR

# Logs
if [[ ! -d $LOGS_DIR ]]; then
        echo "[+] Creating log directories"
        mkdir -p $LOGS_DIR
        chown -R website:website $LOGS_DIR
fi

echo "[+] Reload systemctl"
systemctl daemon-reload
echo "[+] Enable service"
systemctl enable website.service
echo "[+] Start service"
systemctl start website.service
echo "[+] Status:"
systemctl status website.service
