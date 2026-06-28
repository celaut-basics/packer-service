# Node.js (TypeScript) service. TypeScript is compiled in a builder stage; only
# the compiled dist/ and production node_modules reach the runtime filesystem.
FROM node:22-alpine AS builder
WORKDIR /build
COPY ./package.json ./package-lock.json* ./tsconfig.json ./
RUN npm install
COPY ./src ./src
RUN npm run build

FROM node:22-alpine AS deps
WORKDIR /deps
COPY ./package.json ./package-lock.json* ./
RUN npm install --omit=dev

FROM node:22-alpine
WORKDIR /app
COPY --from=deps /deps/node_modules ./node_modules
COPY --from=builder /build/dist ./dist
COPY ./package.json ./
COPY ./start.sh ./start.sh
RUN chmod +x /app/start.sh
