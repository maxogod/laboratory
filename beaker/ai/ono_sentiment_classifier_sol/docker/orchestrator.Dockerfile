ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim-bookworm AS wheel
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir maturin
WORKDIR /src
COPY external/ono/ ./
RUN maturin build --release -m orchestra-py/Cargo.toml -o /wheels

FROM python:${PYTHON_VERSION}-slim-bookworm
COPY --from=wheel /wheels/*.whl /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels
WORKDIR /app
COPY sentiment-classifier/ /opt/sentiment-classifier/
RUN pip install --no-cache-dir /opt/sentiment-classifier

ENTRYPOINT ["sentiment-classifier"]
CMD ["train"]
