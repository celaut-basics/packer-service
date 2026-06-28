# Java (Spring Boot, Gradle) service. bootJar is built in the build stage; only
# the JRE runtime stage filesystem is exported by the packer.
FROM gradle:8.7-jdk21 AS builder
WORKDIR /build
COPY ./build.gradle.kts ./settings.gradle.kts ./
RUN gradle --no-daemon dependencies || true
COPY ./src ./src
RUN gradle --no-daemon bootJar

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=builder /build/build/libs/*.jar /app/app.jar
COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh
