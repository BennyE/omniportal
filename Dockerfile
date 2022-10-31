FROM docker.io/library/python:3.9-alpine

WORKDIR /usr/src/app

RUN apk update && apk upgrade --no-cache

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "./entrypoint.sh" ]