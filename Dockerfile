FROM ubuntu:20.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY /src /app

COPY .env /app

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]