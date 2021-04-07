FROM python:3-slim-buster

RUN apt-get update && apt-get install -y openssl
RUN apt-get install -y git
RUN apt-get install -y python3-pip
RUN pip3 install Flask
RUN /usr/bin/python3 -m pip install flask
RUN apt install -y python3-pyside2*
RUN mkdir -p /var/www/app
RUN chown -R www-data:www-data /var/www/app

RUN apt install -y --no-install-recommends --no-install-suggests cron
RUN apt autoremove

COPY cleanup.sh /usr/local/bin/cleanup.sh
RUN chmod +x /usr/local/bin/cleanup.sh
COPY crontab /etc/cron.d/cleanup-task
RUN chmod 0644 /etc/cron.d/cleanup-task
#RUN service cron enable
#RUN service cron start

CMD /var/www/app/main.py
