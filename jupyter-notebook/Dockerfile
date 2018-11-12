FROM python:3.6-alpine
RUN apk add --no-cache --virtual .build-deps g++ python3-dev libffi-dev openssl-dev
RUN pip install --upgrade pip
RUN pip install jupyter pika redis python-dateutil PyYAML
CMD /usr/local/bin/jupyter notebook --ip=0.0.0.0 --port=8888
