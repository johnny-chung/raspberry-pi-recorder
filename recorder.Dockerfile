FROM python:3.9


WORKDIR /app
RUN apt-get update && \
    apt-get install -y portaudio19-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirement.txt .
RUN pip install -r requirement.txt

COPY app/recorder.py .

RUN apt-get install -y openssh-client

ARG FTP_HOST
ARG FTP_USER

ENV FTP_HOST="$FTP_HOST"
ENV FTP_USER="$FTP_USER" 

CMD ["python", "recorder.py"]