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

docker volume create flo_worker 2> /dev/null
docker volume create flo_worker-ml 2> /dev/null
docker volume create flo_worker-ml_cache 2> /dev/null

#docker network create public_net 2> /dev/null

# supporto per docker compose oltre che per docker-compose
if whereis docker-compose | grep -q '\/'; then
  docker-compose up $dobuild -d
else
  docker compose up $dobuild -d
fi
if docker ps | grep -q 'flo.backend.1'; then
  echo 'Containers were already cleaned up when deploying backend'
else
  for i in $(docker container ls -a | grep '\sExited (.*' | sed 's/\([^ ]*\) *[^ ]* *[^ ]* *.*/\1/g'); do docker container rm $i; done
  for i in $(docker image ls | grep '^<none>.*' | sed 's/[^ ]* *[^ ]* *\([^ ]*\) *.*/\1/g'); do docker image rm $i; done
fi

#TODO: usare rsync --delete invece di cp, per mantenere le cartelle pulite

# Worker
cp -r $appdir/worker/files/* /var/lib/docker/volumes/flo_worker/_data/
git clone https://github.com/zorbaproject/Bran.git /var/lib/docker/volumes/flo_worker/_data/Bran 2> /dev/null | true
cd /var/lib/docker/volumes/flo_worker/_data/Bran
git checkout dev
git pull
cntName=$(docker ps | grep -o 'flo.worker.1')
docker exec $cntName python3 /var/www/app/Bran/main.py help
docker cp $appdir/worker/brancfg $cntName:/root/.brancfg
docker restart $cntName
docker exec $cntName service cron start
docker exec $cntName /bin/bash -c "cat /etc/cron.d/cleanup-task | crontab -"

#Worker-ml
cp -r $appdir/worker-ml/files/* /var/lib/docker/volumes/flo_worker-ml/_data/

