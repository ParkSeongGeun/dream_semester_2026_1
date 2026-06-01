# GitHub Actions vs Jenkins 비교 분석

> 맘편한 이동 백엔드 CI 파이프라인을 13주차(GitHub Actions)와 14주차(Jenkins)에 각각 구축하며 얻은 비교 분석.

## 1. 한눈에 보는 비교표

| 항목 | GitHub Actions | Jenkins |
|------|----------------|---------|
| 형태 | SaaS (GitHub 호스팅) | Self-hosted (직접 설치·운영) |
| 설치/운영 | 불필요 (저장소에 `.yml`만) | 서버·플러그인·업데이트 직접 관리 |
| 설정 언어 | YAML | Groovy (Jenkinsfile) + UI |
| 설정 철학 | 선언적 워크플로우 | Declarative / Scripted 파이프라인 |
| 실행 환경 | GitHub-hosted runner (분당 과금) / self-hosted | 직접 띄운 agent (무제한, 인프라 비용만) |
| 트리거 | push, pull_request, schedule 등 내장 이벤트 | SCM 폴링, Webhook, 수동, cron |
| 플러그인 생태계 | Marketplace Actions | 1,800+ 플러그인 (성숙·방대) |
| 비밀 관리 | Repository/Org Secrets | Credentials 플러그인 + 자격증명 도메인 |
| 초기 진입장벽 | 낮음 (계정만 있으면 즉시) | 높음 (설치·플러그인·보안 설정) |
| 유지보수 부담 | 거의 없음 | 높음 (서버·플러그인 CVE 대응) |
| 확장성 | runner 추가 (관리형) | agent 노드 자유 확장 |
| 비용 모델 | 공개 저장소 무료 / 사설 분당 과금 | 도구 무료, 인프라·운영 인건비 발생 |

## 2. 설정 방식 비교 (실제 프로젝트 코드 기준)

### 2-1. GitHub Actions — 선언적 YAML (13주차 `.github/workflows/ci.yml`)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pytest tests/ --cov=app
```

- Job 간 순서는 `needs`로 선언
- DB/캐시는 `services` 블록으로 손쉽게 사이드카 기동
- `uses:`로 Marketplace Action 재사용

### 2-2. Jenkins — Declarative Pipeline (14주차 `Jenkinsfile`)

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                dir('backend') {
                    sh '. .venv/bin/activate && pytest tests/ --cov=app'
                }
            }
        }
    }
    post {
        always { junit 'backend/test-results/junit.xml' }
    }
}
```

- `stages { stage { steps } }` 구조의 단계 정의
- `post { success / failure / always }`로 후처리(알림·아티팩트) 선언
- Groovy 기반이라 조건·반복 등 프로그래밍 로직을 직접 작성 가능

## 3. Declarative vs Scripted 파이프라인 (Jenkins 고유)

Jenkins는 동일한 파이프라인을 두 문법으로 작성할 수 있다.

| 구분 | Declarative | Scripted |
|------|-------------|----------|
| 문법 | `pipeline { }` 정형 구조 | `node { }` 안에 Groovy 코드 |
| 가독성 | 높음 (선언적) | 낮음 (절차적) |
| 유연성 | 제한적 (정해진 디렉티브) | 매우 높음 (완전한 Groovy) |
| 권장 | 대부분의 경우 | 복잡한 동적 로직이 필요할 때 |
| 오류 검증 | 사전 검증 강함 | 런타임에 발견 |

본 프로젝트는 가독성과 유지보수성을 위해 **Declarative**를 채택하였다. GitHub Actions의 YAML이 선언적인 것과 같은 맥락이다.

## 4. 동일 파이프라인, 다른 구현

13주차와 14주차는 **같은 5단계 파이프라인**(Checkout → Build → Lint → Test → Docker Build → Push to ECR)을 서로 다른 도구로 구현했다. 핵심 차이는 다음과 같다.

- **DB/캐시 의존성**: GitHub Actions는 `services`로 postgres/redis를 선언만 하면 됐지만, Jenkins는 별도 설계가 필요하다. 본 프로젝트는 `conftest.py`의 SQLite 인메모리 DI override 덕분에 외부 서비스 없이 테스트가 돌아가, Jenkins built-in 노드에서 `python venv + pytest`만으로 동일 테스트를 수행했다.
- **Docker 빌드**: GitHub runner는 docker가 기본 제공된다. Jenkins는 컨테이너 안에서 host의 `docker.sock`을 마운트(Docker outside of Docker)하여 빌드한다.
- **설정의 코드화**: GitHub Actions는 워크플로우 자체가 곧 코드다. Jenkins는 서버·플러그인·계정·Job까지 코드화하기 위해 **JCasC(Configuration as Code)** 와 **Job DSL**을 추가로 도입했다.

## 5. 언제 무엇을 쓰는가

- **GitHub Actions가 유리한 경우**: GitHub에 코드가 있고, 별도 인프라 운영 인력이 없으며, 빠르게 CI를 붙이고 싶을 때. 스타트업·개인·오픈소스에 적합.
- **Jenkins가 유리한 경우**: 온프레미스/폐쇄망 요구, 복잡한 빌드 매트릭스, 기존 Jenkins 자산, 분당 과금이 부담되는 대규모 빌드, 세밀한 플러그인 커스터마이징이 필요할 때. 엔터프라이즈에 적합.

## 6. 결론

맘편한 이동 프로젝트 규모에서는 **GitHub Actions가 운영 부담 측면에서 우월**하다. 다만 Jenkins를 직접 구축하며 Pipeline as Code, JCasC, 플러그인 생태계, self-hosted CI의 동작 원리를 학습한 것은 두 도구를 상황에 맞게 선택할 수 있는 판단 기준을 갖추게 했다는 점에서 의미가 있다.
