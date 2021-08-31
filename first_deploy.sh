#!/bin/bash
appdir=$(dirname "$(readlink -f "$0")")
docker volume create flo_backend 2> /dev/null
docker volume create flo_frontend 2> /dev/null
docker volume create flo_deploy 2> /dev/null

docker network create public_net 2> /dev/null

docker-compose up --build -d
for i in $(docker container ls -a | grep '\sExited (.*' | sed 's/\([^ ]*\) *[^ ]* *[^ ]* *.*/\1/g'); do docker container rm $i; done
for i in $(docker image ls | grep '^<none>.*' | sed 's/[^ ]* *[^ ]* *\([^ ]*\) *.*/\1/g'); do docker image rm $i; done


# Backend
cp -r $appdir/backend/files/* /var/lib/docker/volumes/flo_backend/_data/
git clone https://github.com/zorbaproject/Bran.git /var/lib/docker/volumes/flo_backend/_data/Bran 2> /dev/null | true
cd /var/lib/docker/volumes/flo_backend/_data/Bran
git checkout dev
git pull
chmod +x /var/lib/docker/volumes/flo_backend/_data/main.py
docker exec flo_backend_1 python3 /var/www/app/Bran/main.py help
docker cp $appdir/backend/brancfg flo_backend_1:/root/.brancfg
docker restart flo_backend_1
docker exec flo_backend_1 service cron start
docker exec flo_backend_1 cat /etc/cron.d/cleanup-task | crontab -

# Frontend
cp -r $appdir/frontend/files/* /var/lib/docker/volumes/flo_frontend/_data/
