FROM python:3.9.16-bullseye

WORKDIR /elbot/
COPY . .

RUN pip install -r requirements.txt

RUN apt update; apt-get install -yy apache2

CMD ["bash","run.sh"]