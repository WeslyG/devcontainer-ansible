FROM mcr.microsoft.com/devcontainers/python:2-3.12-bookworm

COPY requirements.txt .
COPY platform_version.txt /etc/platform_version

RUN pip3 install -r requirements.txt
