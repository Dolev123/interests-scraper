FROM alpine:latest

RUN apk add vim git python3

RUN adduser -u 1001 -D user
WORKDIR /home/user
USER 1001

RUN git clone https://github.com/Dolev123/interests-scraper.git
WORKDIR /home/user/interests-scraper
ENV WORK_DIR=/home/user/interests-scraper
RUN python -m venv . && . bin/activate && pip install -r requirements.txt

EXPOSE 8080/tcp

CMD ["/bin/sh", "./run.sh"]
