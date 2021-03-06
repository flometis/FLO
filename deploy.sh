#!/bin/bash
appdir=$(dirname "$(readlink -f "$0")")

cd $appdir
fromccommit=$(git log -n1 | head -n1 | sed "s/commit \([a-z0-9]*\)[ ]*.*/\1/g")
git pull
echo "Files changed:"
git diff --name-only $fromccommit HEAD
echo "----"
dobuild=""
if git diff --name-only $fromccommit HEAD | grep -q "Dockerfile"; then 
  echo "Dockerfile changed, forcing BUILD"
  dobuild="--build"
fi

docker volume create flo_backend 2> /dev/null
docker volume create flo_frontend 2> /dev/null
docker volume create flo_deploy 2> /dev/null

docker network create public_net 2> /dev/null

docker-compose up $dobuild -d
for i in $(docker container ls -a | grep '\sExited (.*' | sed 's/\([^ ]*\) *[^ ]* *[^ ]* *.*/\1/g'); do docker container rm $i; done
for i in $(docker image ls | grep '^<none>.*' | sed 's/[^ ]* *[^ ]* *\([^ ]*\) *.*/\1/g'); do docker image rm $i; done

#TODO: usare rsync --delete invece di cp, per mantenere le cartelle pulite

#Deploy
cp -r $appdir/deploy/files/* /var/lib/docker/volumes/flo_deploy/_data/
cronjob="*/2 * * * * $appdir/deploy/deployonpush.sh '/var/lib/docker/volumes/flo_deploy/_data/deploy.request' '$appdir/deploy.sh' 'FLO'"
if ! crontab -l | grep -q "$appdir/deploy/deployonpush.sh"; then
 (crontab -l 2>/dev/null; echo "$cronjob") | crontab -
fi

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
docker exec flo_backend_1 /bin/bash -c "cat /etc/cron.d/cleanup-task | crontab -"

# Frontend
cp -r $appdir/frontend/files/* /var/lib/docker/volumes/flo_frontend/_data/
