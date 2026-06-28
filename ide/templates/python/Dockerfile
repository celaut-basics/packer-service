# Multi-stage Python service. The build only produces a FILESYSTEM that the
# packer exports — do not add CMD/ENTRYPOINT/EXPOSE (see SERVICE_CONFIG_GUIDE.md).
FROM python:3.11-slim AS builder
WORKDIR /install
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY ./src /app/src
COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh
