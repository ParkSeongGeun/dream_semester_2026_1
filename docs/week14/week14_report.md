# 14주차 활동 보고서

## 1. 프로젝트 주차 목표

Jenkins를 Docker로 설치하고 맘편한 이동 백엔드의 CI 파이프라인을 구축한다. Pipeline as Code 개념을 학습하고 Jenkinsfile 작성법을 익히며, 선언적(Declarative)과 스크립트(Scripted) 파이프라인의 차이를 이해한다. 파이프라인 단계는 Checkout → Build/Lint → Test → Docker Build → Push to ECR로 구성한다. 13주차에 구축한 GitHub Actions와 동일한 단계를 Jenkins로 재구현하여 두 도구의 차이점을 실증적으로 비교 분석한다. 단순히 설정 파일을 작성하는 데 그치지 않고, Jenkins를 실제로 기동하여 파이프라인이 SUCCESS로 완료되는 것을 검증하는 것을 핵심 목표로 한다.


## 2. 프로젝트 주차 진행 내용

### 2-1. JCasC 기반 Jenkins 코드화 (infra/jenkins/)

Jenkins를 단순히 설치하는 대신, Pipeline as Code 정신에 맞춰 **JCasC(Jenkins Configuration as Code)** 로 서버 구성 전체를 코드화하였다. 이로써 Setup Wizard의 수동 작업(초기 비밀번호 입력, 플러그인 선택, 관리자 계정 생성) 없이 `docker compose up` 한 번으로 동일한 Jenkins 환경이 재현된다.

- **Dockerfile**: `jenkins/jenkins:lts-jdk17`을 베이스로 Python3, Docker CLI, buildx, git을 설치하고 `plugins.txt`의 플러그인을 사전 설치하였다.
- **plugins.txt**: configuration-as-code, workflow-aggregator(Pipeline), job-dsl, docker-workflow, git, github, credentials, slack 등을 명시하였다.
- **casc.yaml**: 관리자 계정(환경변수 주입), 권한 전략, 시스템 URL, 그리고 Job DSL로 `comfortablemove-backend` 파이프라인 Job을 정의하였다. 이 Job은 GitHub 저장소를 체크아웃하고 루트의 Jenkinsfile을 실행한다.
- **docker-compose.yml**: 포트(8080, 50000), named volume(jenkins_home), 그리고 host의 `docker.sock`을 마운트하여 컨테이너 안에서 host Docker로 이미지를 빌드하는 DooD(Docker outside of Docker) 구조를 구성하였다.

JCasC 설정 파일은 named volume에 가려지지 않도록 `/usr/share/jenkins/ref/` 경로에 배치하고 `CASC_JENKINS_CONFIG`로 지정하였다.

### 2-2. Declarative Jenkinsfile 작성

루트에 Declarative 파이프라인 `Jenkinsfile`을 작성하였다. 13주차 GitHub Actions의 lint → test → build 흐름을 그대로 옮겼다.

- **Checkout**: `checkout scm`으로 저장소를 가져오고 commit SHA 앞 7자리를 이미지 태그로 사용한다.
- **Lint**: flake8는 순수 파이썬이므로 Jenkins 노드의 venv에서 직접 실행한다.
- **Test**: `Dockerfile.test`(python:3.12-slim 기반)를 빌드하여 컨테이너 안에서 pytest를 실행한다. 테스트 후 junit XML을 `docker cp`로 추출하여 Jenkins에 게시한다.
- **Docker Build**: 운영 이미지를 빌드한다.
- **Push to ECR**: `ECR_REGISTRY` 환경변수가 주입된 경우에만 실행되도록 `when` 조건을 두어, 미설정 시 graceful skip 한다.
- **post**: 빌드 산출물 정리와 Slack 알림(SLACK_CHANNEL 설정 시)을 처리한다.

선언적/스크립트 파이프라인 중, 가독성과 사전 오류 검증이 강한 **Declarative**를 채택하였다. 이는 GitHub Actions의 YAML이 선언적인 것과 같은 맥락이다.

### 2-3. 파이프라인 실제 기동 및 디버깅 (핵심)

Jenkins 컨테이너를 실제로 기동하고 REST API(crumb 인증)로 파이프라인을 트리거하며, SUCCESS가 나올 때까지 5회에 걸쳐 디버깅하였다. 매 실패의 원인을 콘솔 로그로 추적하고 수정하였다(상세는 4장).

최종적으로 **빌드 #5가 SUCCESS(49초)** 로 완료되었으며 단계별 결과는 다음과 같다.

| 단계 | 결과 | 소요 |
|------|------|------|
| Checkout | SUCCESS | 1s |
| Lint (flake8) | SUCCESS | 2s |
| Test (pytest) | SUCCESS (77 passed) | 8s |
| Docker Build | SUCCESS | 32s |
| Push to ECR | NOT_EXECUTED (graceful skip) | - |

JUnit 테스트 리포트(passCount 77, failCount 0)가 Jenkins UI에 정상 게시되었다.

### 2-4. Webhook · 멀티브랜치 · Slack 알림

- **Slack 알림**: Jenkinsfile의 post 단계에 `slackSend`를 작성하여 빌드 결과(성공 green / 실패 red)를 발송하도록 구성하였다. SLACK_CHANNEL 환경변수가 있을 때만 동작하며, 봇 토큰은 별도 발급이 필요해 실제 메시지 수신은 검증하지 못하였다.
- **GitHub Webhook / 멀티브랜치**: 로컬 Jenkins는 외부 공인 URL이 없어 GitHub가 Webhook을 직접 호출할 수 없다. 본 주차에서는 REST API 트리거로 파이프라인 동작을 검증하였고, 운영 시에는 Webhook 또는 SCM 폴링으로 자동 트리거하도록 전환하는 방향을 정리하였다.

### 2-5. GitHub Actions vs Jenkins 비교 분석

13주차(GitHub Actions)와 14주차(Jenkins)에 동일한 5단계 파이프라인을 구현한 경험을 바탕으로 비교 문서를 작성하였다(`docs/week14/github_actions_vs_jenkins.md`). 호스팅 방식(SaaS vs self-hosted), 설정 언어(YAML vs Groovy), DB/캐시 의존성 처리, 설정 코드화 범위, 운영 부담, 비용 모델 등을 표로 정리하였다.


## 3. 프로젝트 주차 진행 결과

JCasC 기반 Jenkins 환경 완성: `docker compose up --build` 한 번으로 관리자 계정·플러그인·파이프라인 Job이 자동 구성되는 재현 가능한 CI 환경을 구축하였다.

파이프라인 실제 동작 검증: 빌드 #5가 Checkout → Lint → Test → Docker Build 전 단계를 통과하여 SUCCESS로 완료되었다. pytest 77건 통과, 운영 이미지 빌드 성공을 콘솔 로그와 JUnit 리포트로 확인하였다.

ARM64 환경 대응: Jenkins 노드에서의 네이티브 컴파일 실패를 공식 python 이미지 기반 Docker 빌드로 우회하여, 환경 차이에 영향받지 않는 테스트 단계를 구성하였다.

Push to ECR graceful skip: ECR 자격증명이 없어도 lint/test/빌드가 정상 수행되어, 배포 인프라 없이도 파이프라인 검증이 가능하다.

비교 분석 문서화: GitHub Actions와 Jenkins의 장단점을 실제 프로젝트 코드 기준으로 비교하여 상황별 선택 기준을 정리하였다.

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1


## 4. 기타 (문제점, 해결방법, 자기평가)

### 4-1. 문제점 및 해결방법

**timestamps() 옵션 미지원**: Jenkinsfile options에 `timestamps()`를 넣었으나 timestamper 플러그인이 설치되지 않아 컴파일 단계에서 실패하였다. 해당 옵션은 부가 기능이므로 제거하여 해결하였다. 설치된 플러그인이 지원하는 디렉티브만 사용해야 함을 학습하였다.

**ARM64 네이티브 컴파일 실패**: Jenkins 노드(ARM64)에서 직접 `pip install`을 수행하니 asyncpg와 pydantic-core가 해당 파이썬 버전의 wheel을 찾지 못해 소스 빌드로 전환되었고, gcc/cargo가 없어 실패하였다. 테스트/빌드를 공식 python:3.12-slim 기반 Docker 이미지 안에서 수행하도록 전환하여, wheel이 정상 제공되는 환경에서 빌드되게 함으로써 해결하였다.

**.dockerignore의 tests/ 제외**: 운영용 `.dockerignore`가 tests/를 제외하고 있어 테스트 이미지 빌드 시 `COPY tests/`가 실패하였다. 운영 설정을 건드리지 않기 위해, BuildKit의 per-Dockerfile ignore 기능을 활용해 `Dockerfile.test.dockerignore`를 별도로 작성하여 테스트 빌드에서만 tests/를 포함시켰다.

**buildx 컴포넌트 누락**: per-Dockerfile ignore는 BuildKit 전용 기능인데, Jenkins 컨테이너의 docker CLI에 buildx 컴포넌트가 없어 "BuildKit is enabled but buildx is missing" 오류가 발생하였다. Jenkins 이미지에 docker-buildx-plugin을 추가 설치하고 재빌드하여 해결하였다. 동일한 docker build 명령이 호스트(Mac)에서는 성공하고 컨테이너에서는 실패한 원인이 buildx 유무였음을 확인하며, 빌드 도구의 환경 의존성을 체감하였다.

### 4-2. 자기평가

Jenkins를 단순히 설치하는 수준을 넘어, JCasC로 서버 구성 전체를 코드화하고 실제로 기동하여 파이프라인이 SUCCESS로 완료되는 것까지 검증하였다. 특히 5회의 빌드 실패를 콘솔 로그로 추적하며 원인을 좁혀가는 과정에서, CI 도구가 추상화해주던 부분(러너에 미리 깔린 docker/python, wheel 제공, 빌드 컨텍스트 처리)을 self-hosted 환경에서는 직접 구성해야 한다는 점을 명확히 이해하였다.

13주차 GitHub Actions와 동일한 파이프라인을 Jenkins로 재구현하면서, 같은 목표라도 도구에 따라 구현 난이도와 책임 범위가 크게 달라짐을 비교 관점에서 학습하였다. GitHub Actions가 `services` 한 줄로 처리하던 의존성을, Jenkins에서는 conftest의 SQLite override를 활용해 우회하는 등 도구의 제약에 맞춰 설계를 조정하는 경험을 하였다.

아쉬운 점은 GitHub Webhook 자동 트리거와 Slack 실제 알림 수신까지는 검증하지 못한 것이다. 로컬 Jenkins의 외부 접근 제약(공인 URL 부재)과 Slack 봇 토큰 미발급 때문이며, 설정 자체는 코드로 작성해 두었으므로 공개 서버나 ngrok, 토큰이 확보되면 즉시 동작 가능한 상태이다.
