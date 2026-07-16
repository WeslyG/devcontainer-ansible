FROM python:3.13-trixie

COPY requirements.txt .
COPY platform_version.txt /etc/platform_version

RUN pip3 install -r requirements.txt
