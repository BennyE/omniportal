FROM docker.io/library/python:3.9-alpine

WORKDIR /usr/src/app

RUN uname -m

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "./entrypoint.sh" ]