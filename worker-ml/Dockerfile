FROM python:3.10
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update; apt-get install -y vim wget curl w3m 
#RUN apt-get install -y software-properties-common

RUN apt-get install -y python3-pip
RUN python3 -m pip install --upgrade pip setuptools wheel 

#RUN pip3 install torch

RUN mkdir -p /app
COPY ./requirements.txt /tmp/requirements.txt
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

#Install requirements
#RUN pip3 install torch==1.12.1+cu113 -f https://nelsonliu.me/files/pytorch/whl/torch_stable.html
RUN pip3 install -r /tmp/requirements.txt

CMD /entrypoint.sh
