FROM docker.io/library/python:3-slim-bullseye

RUN apt update && apt dist-upgrade -y && apt clean

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "./entrypoint.sh" ]