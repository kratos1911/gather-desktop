FROM python:3.12.14-slim-trixie@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b
RUN apt-get update && apt-get install -y --no-install-recommends build-essential dpkg-dev debhelper autoconf xz-utils patch \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
