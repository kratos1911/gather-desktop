FROM python:3.12.14-slim-trixie@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b
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
COPY services/worker/*.py /app/services/worker/
USER 65532:65532
ENTRYPOINT ["python", "-m", "services.worker.extractor_runner"]
