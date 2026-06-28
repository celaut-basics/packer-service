# Node.js (Express) service. Production deps are installed in a builder stage
# and copied into a clean runtime stage.
FROM node:22-alpine AS builder
WORKDIR /build
COPY ./package.json ./package-lock.json* ./
RUN npm install --omit=dev

FROM node:22-alpine
WORKDIR /app
COPY --from=builder /build/node_modules ./node_modules
COPY ./src ./src
COPY ./package.json ./
COPY ./start.sh ./start.sh
RUN chmod +x /app/start.sh
