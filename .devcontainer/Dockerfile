FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

COPY requirements.txt .
COPY platform_version.txt /etc/platform_version

RUN pip3 install -r requirements.txt

RUN apt-get update && apt-get install -y nodejs npm\
    && npm install -g elasticdump
