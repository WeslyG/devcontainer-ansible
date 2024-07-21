FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

COPY requirements.txt .
COPY platform_verion.txt /etc/platform_verion

RUN pip3 install -r requirements.txt
