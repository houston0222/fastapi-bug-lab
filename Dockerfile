FROM python:3.14-slim

WORKDIR /workspace

COPY pyproject.toml .

RUN pip install --no-cache-dir .

CMD ["sleep", "infinity"]