FROM nginx:1.19.2

RUN apt-get update && apt-get install -y openssl
RUN openssl req -x509 -nodes -days 2000 -subj "/C=CA/ST=QC/O=Company, Inc./CN=localhost" -addext "subjectAltName=DNS:localhost" -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt;
RUN mkdir -p /var/www/app
RUN chown www-data:www-data /var/www/app
COPY files/ /var/www/app

