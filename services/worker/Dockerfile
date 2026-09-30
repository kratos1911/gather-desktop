FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/worker/requirements-extraction.txt /app/requirements-extraction.txt
RUN pip install --no-cache-dir -r /app/requirements-extraction.txt
COPY services/worker/*.py /app/services/worker/
USER 65532:65532
ENTRYPOINT ["python", "-m", "services.worker.extractor_runner"]
