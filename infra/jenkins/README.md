# Jenkins CI (맘편한 이동) — 14주차

Pipeline as Code로 구성한 로컬 Jenkins CI 환경. **JCasC(Configuration as Code)** 로 관리자 계정·플러그인·파이프라인 Job을 모두 코드로 정의하여, Setup Wizard 수동 작업 없이 `docker compose up` 한 번으로 재현된다.

## 구성 파일

| 파일 | 역할 |
|------|------|
| `Dockerfile` | jenkins-lts + Python3 + Docker CLI + buildx + 플러그인 사전 설치 |
| `plugins.txt` | 설치 플러그인 목록 (JCasC, Pipeline, Job DSL, docker-workflow 등) |
| `casc.yaml` | 관리자 계정·권한·파이프라인 Job을 코드로 정의 |
| `docker-compose.yml` | 컨테이너 실행 (docker.sock 공유로 DooD 빌드 지원) |
| `.env.example` | 관리자 계정/Slack/ECR 환경변수 템플릿 |

## 실행

```bash
cp .env.example .env          # 필요 시 비밀번호 수정
docker compose up -d --build  # 이미지 빌드 + 기동
# http://localhost:8080  (admin / admin123!)
```

기동 후 `comfortablemove-backend` 파이프라인 Job이 JCasC에 의해 자동 생성된다. 이 Job은 GitHub 저장소를 체크아웃하고 루트의 `Jenkinsfile`을 실행한다.

## 파이프라인 (루트 `Jenkinsfile`)

```
Checkout → Lint(flake8) → Test(pytest) → Docker Build → Push to ECR
```

- **Lint**: flake8는 순수 파이썬이라 Jenkins 노드 venv에서 직접 실행
- **Test**: `Dockerfile.test`(python:3.12-slim)를 빌드해 컨테이너 안에서 pytest 실행 → ARM64 네이티브 컴파일 회피
- **Docker Build**: 운영 이미지 빌드
- **Push to ECR**: `ECR_REGISTRY` 환경변수가 있을 때만 실행 (미설정 시 graceful skip)

## 빌드 수동 트리거 (REST API)

로컬 Jenkins는 외부 공인 URL이 없어 GitHub Webhook을 직접 받기 어렵다. 대신 REST API로 트리거하여 동작을 검증할 수 있다.

```bash
JAR=$(mktemp)
CRUMB=$(curl -s -c "$JAR" -u admin:admin123! \
  'http://localhost:8080/crumbIssuer/api/json' | python3 -c "import sys,json;print(json.load(sys.stdin)['crumb'])")
curl -s -b "$JAR" -u admin:admin123! -H "Jenkins-Crumb: $CRUMB" \
  -X POST 'http://localhost:8080/job/comfortablemove-backend/build'
```

운영 환경에서는 GitHub Webhook 또는 SCM 폴링으로 push 시 자동 트리거하도록 전환한다.

## 보안 노트

- 로컬 학습 환경이라 `user: root` + `docker.sock` 마운트(DooD)를 사용한다. 운영에서는 권한 분리(rootless, sidecar agent, Kaniko 등)를 권장한다.
- `.env`는 비밀번호/토큰을 포함하므로 `.gitignore` 처리되어 있다 (`.env.example`만 커밋).
