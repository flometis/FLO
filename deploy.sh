#!/bin/bash
appdir=$(dirname "$(readlink -f "$0")")
docker-compose up --build -d
for i in $(docker image ls | grep '^<none>.*' | sed 's/[^ ]* *[^ ]* *\([^ ]*\) *.*/\1/g'); do docker image rm $i; done


# Backend
cp -r /root/flo/backend/files/* /var/lib/docker/volumes/flo_backend/_data/
git clone https://github.com/zorbaproject/Bran.git /var/lib/docker/volumes/flo_backend/_data/Bran 2> /dev/null | true
cd /var/lib/docker/volumes/flo_backend/_data/Bran
git checkout dev
git pull
chmod +x /var/lib/docker/volumes/flo_backend/_data/main.py
docker exec flo_backend_1 python3 /var/www/app/Bran/main.py help

# Frontend
cp -r /root/flo/frontend/files/* /var/lib/docker/volumes/flo_frontend/_data/
