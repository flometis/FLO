FROM nginx:latest

RUN apt-get update && apt-get install -y openssl wget curl w3m vim unzip
#RUN openssl req -x509 -nodes -days 2000 -subj "/C=CA/ST=QC/O=Company, Inc./CN=localhost" -addext "subjectAltName=DNS:localhost" -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt;
RUN apt-get install nginx-extras
RUN apt-get install libnginx-mod-http-headers-more-filter

RUN mkdir -p /var/www/app
RUN chown www-data:www-data /var/www/app
COPY files/ /var/www/app

RUN mkdir -p /var/www/app/bootstrap-italia
RUN wget -O /var/www/app/bootstrap-italia/bootstrap-italia.zip https://github.com/italia/bootstrap-italia/releases/download/v1.4.3/bootstrap-italia.zip
RUN cd /var/www/app/bootstrap-italia && unzip -o /var/www/app/bootstrap-italia/bootstrap-italia.zip
