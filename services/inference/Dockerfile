FROM python:3.12.14-slim-trixie@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_XET=1 TOKENIZERS_PARALLELISM=false HF_HOME=/tmp/hf HOME=/tmp OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
WORKDIR /app
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       openssl=3.5.7-1~deb13u3 \
       libssl3t64=3.5.7-1~deb13u3 \
       openssl-provider-legacy=3.5.7-1~deb13u3 \
       libpcre2-8-0=10.46-1~deb13u3 \
    && rm -rf /var/lib/apt/lists/*
# Context is explicitly staged on D:; no repository secrets or model weights.
COPY requirements.lock /app/requirements.lock
RUN --mount=type=bind,source=wheels,target=/wheels python -m pip --isolated install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r /app/requirements.lock \
    && python -m pip check \
    && python -m pip uninstall --yes pip \
    && python -c "import pathlib, shutil, sysconfig; shutil.rmtree(pathlib.Path(sysconfig.get_path('stdlib')) / 'ensurepip')"
COPY services /app/services
COPY third-party-notices.json /app/third-party-notices.json
USER 65532:65532
ENTRYPOINT ["python", "-m", "services.inference.stream"]
