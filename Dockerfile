FROM python:3.12.5-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git gcc libpq-dev python3-dev curl binutils \
    libproj-dev libgdal-dev python3-gdal gdal-bin \
    gnome-terminal \
    && python -m pip install --upgrade pip

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app

RUN chmod +x /app/start.sh
