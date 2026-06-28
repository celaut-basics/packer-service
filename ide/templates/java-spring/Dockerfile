# Java (Spring Boot, Maven) service. The fat JAR is assembled in the build stage;
# only the JRE runtime stage filesystem is exported by the packer.
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
COPY ./pom.xml .
RUN mvn -B dependency:go-offline
COPY ./src ./src
RUN mvn -B package -DskipTests

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=builder /build/target/*.jar /app/app.jar
COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh
