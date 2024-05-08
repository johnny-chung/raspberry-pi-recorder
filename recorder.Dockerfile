FROM python:3.9

WORKDIR /app

COPY requirement.txt .
RUN pip install -r requirement.txt

COPY app/ .

RUN apt-get update && apt-get install -y openssh-client

ARG FTP_HOST
ARG FTP_USER
ARG FTP_PASSWORD

ENV FTP_HOST="$FTP_HOST"
ENV FTP_USER="$FTP_USER"
ENV FTP_PASSWORD="$FTP_PASSWORD" 

CMD ["python", "recorder.py"]