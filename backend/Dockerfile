FROM python:3-slim-buster

RUN apt-get update && apt-get install -y openssl
#RUN apt-get install -y openssh-server
RUN apt-get install -y git
RUN apt-get install -y python3-pip
RUN pip3 install Flask
RUN apt install python3-pyside2*
RUN mkdir -p /var/www/app
RUN chown -R www-data:www-data /var/www/app

CMD python3 /var/www/app/main.py

#EXPOSE 22

