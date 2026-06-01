# ============================================
# 맘편한 이동 - Jenkins 커스텀 이미지
# jenkins/jenkins:lts + Python 3 + Docker CLI + 플러그인 사전 설치
# ============================================
FROM jenkins/jenkins:lts-jdk17

USER root

# Python 3 (빌드/테스트용) + Docker CLI (이미지 빌드용) + git 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip git \
        ca-certificates curl gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin && \
    rm -rf /var/lib/apt/lists/*

# 플러그인 사전 설치 (Setup Wizard 없이 코드로 관리)
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# JCasC 설정 파일 위치 지정
# 주의: /var/jenkins_home 은 named volume 으로 덮이므로 그 바깥 경로에 둔다.
COPY casc.yaml /usr/share/jenkins/ref/casc.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml

# Setup Wizard 비활성화 (계정/플러그인을 코드로 관리하므로)
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
