FROM python:3.12.14-slim-trixie@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b AS installer
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/worker/requirements-bootstrap.lock /app/requirements-bootstrap.lock
RUN python -m pip --isolated install --no-cache-dir --disable-pip-version-check \
    --index-url https://pypi.org/simple --only-binary=:all: --require-hashes \
    -r /app/requirements-bootstrap.lock
COPY services/worker/requirements-extraction.lock /app/requirements-extraction.lock
RUN python -m pip --isolated install --no-cache-dir --disable-pip-version-check \
    --index-url https://pypi.org/simple --only-binary=:all: --require-hashes \
    -r /app/requirements-extraction.lock \
    && python -m pip check

FROM installer AS runtime
# Exact Debian security versions; fail rather than silently select replacements.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       openssl=3.5.7-1~deb13u3 \
       libssl3t64=3.5.7-1~deb13u3 \
       openssl-provider-legacy=3.5.7-1~deb13u3 \
       libpcre2-8-0=10.46-1~deb13u3 \
    && rm -rf /var/lib/apt/lists/*
# Remove installer code AND its bootstrap wheel, not just executable wrappers.
RUN python -m pip uninstall --yes pip \
    && python -c "import pathlib, shutil, sysconfig; shutil.rmtree(pathlib.Path(sysconfig.get_path('stdlib')) / 'ensurepip')"
COPY services/worker/*.py /app/services/worker/
USER 65532:65532
ENTRYPOINT ["python", "-m", "services.worker.extractor_runner"]
