# Go compiled-binary service. Only the final stage's filesystem is exported.
FROM golang:1.22 AS builder
WORKDIR /src
COPY ./src /src
RUN CGO_ENABLED=0 go build -o /out/myservice .

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /out/myservice /app/myservice
COPY ./start.sh /app/start.sh
RUN chmod +x /app/myservice /app/start.sh
