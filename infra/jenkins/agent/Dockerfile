FROM eclipse-temurin:21-jre-jammy AS java
FROM jenkins/inbound-agent:jdk21 AS remoting
FROM docker:cli AS dockercli
FROM aquasec/trivy:latest AS trivy

FROM python:3.12-slim-bookworm

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git curl ca-certificates libstdc++6 libgcc-s1 zlib1g libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=java /opt/java/openjdk /opt/java/openjdk
COPY --from=remoting /usr/share/jenkins/agent.jar /usr/share/jenkins/agent.jar
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=trivy /usr/local/bin/trivy /usr/local/bin/trivy

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/semgrep/bin:/opt/java/openjdk/bin:${PATH}
RUN python3 -m venv /opt/semgrep \
    && /opt/semgrep/bin/pip install --no-cache-dir semgrep \
    && groupadd --gid 1000 jenkins \
    && useradd --uid 1000 --gid jenkins --create-home jenkins \
    && mkdir -p /home/jenkins/agent \
    && chown jenkins:jenkins /home/jenkins/agent

RUN java -version \
    && python3 --version \
    && git --version \
    && docker --version \
    && trivy --version \
    && semgrep --version

USER jenkins
WORKDIR /home/jenkins/agent
ENTRYPOINT ["java", "-jar", "/usr/share/jenkins/agent.jar"]
