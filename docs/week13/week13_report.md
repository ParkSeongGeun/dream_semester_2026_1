# 13주차 활동 보고서

## 1. 프로젝트 주차 목표

GitHub Actions를 활용하여 맘편한 이동 백엔드의 CI 파이프라인을 구축한다. Workflow, Job, Step, Runner, Event 등 핵심 개념을 학습하고 YAML로 워크플로우 파일을 작성하는 방법을 익힌다. 파이프라인 단계는 코드 체크아웃 → Python 환경 설정 → 의존성 설치 → 린트(flake8) → 테스트(pytest) → Docker 이미지 빌드 → ECR 푸시로 구성하며, push와 pull_request 이벤트를 트리거로 설정한다. GitHub Secrets로 AWS 인증 정보를 관리하고, 의존성 캐싱으로 빌드 시간을 단축한다.


## 2. 프로젝트 주차 진행 내용

### 2-1. GitHub Actions 핵심 개념 학습

GitHub Actions의 구성 요소를 실습을 통해 학습하였다.

- **Workflow**: `.github/workflows/` 디렉터리에 저장되는 자동화 단위. 하나 이상의 Job으로 구성된다.
- **Event**: 워크플로우를 트리거하는 이벤트. `push`, `pull_request`, `schedule` 등이 있으며 이번 파이프라인에서는 `push`와 `pull_request`를 사용한다.
- **Job**: 독립적으로 실행되는 작업 단위. `needs` 키워드로 순서 의존성을 지정한다.
- **Step**: Job 내의 개별 실행 단계. `uses`로 Action을 호출하거나 `run`으로 쉘 명령을 실행한다.
- **Runner**: Job이 실행되는 가상 머신. `ubuntu-latest`를 사용하였다.


### 2-2. CI 파이프라인 구성 (.github/workflows/ci.yml)

기존에 작성된 ci.yml에 lint 단계가 없고 ECR 푸시가 누락되어 있었다. 이를 다음 3-Job 구조로 재구성하였다.

**Job 1: lint (flake8)**

`actions/setup-python@v5`의 pip cache 기능을 활성화하여 의존성 캐싱을 적용하였다. flake8를 설치하고 `app/` 디렉터리에 대해 정적 분석을 실행한다. 이 Job이 실패하면 이후 Job은 실행되지 않는다.

**Job 2: test (pytest, needs: lint)**

lint Job 통과 후 실행된다. `services` 블록에 postgres:15와 redis:7을 올려 실제 데이터베이스와 캐시가 필요한 통합 테스트까지 수행할 수 있도록 하였다. `actions/setup-python@v5`의 `cache: pip` 옵션으로 requirements.txt 기반 캐싱을 적용하여 반복 실행 시 의존성 설치 시간을 단축하였다. pytest 실행 시 `--cov=app --cov-report=xml` 옵션으로 커버리지 리포트를 생성하고, `actions/upload-artifact@v4`로 7일간 보관한다.

**Job 3: build-and-push (Docker, needs: test)**

test Job 통과 후 실행된다. Docker 이미지를 항상 빌드하여 Dockerfile 오류를 조기에 탐지한다. ECR 푸시는 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `ECR_REGISTRY` 세 Secrets가 모두 등록된 경우에만, main 브랜치 push 이벤트에서 실행된다. Secrets 미등록 시 `::warning::` 메시지를 남기고 건너뛰어 파이프라인이 실패하지 않도록 하였다. ECR 푸시 시 commit SHA 태그와 latest 태그를 동시에 부여한다.

```yaml
on:
  pull_request:
    branches: [main]
    paths:
      - 'backend/**'
  push:
    branches: [main]
    paths:
      - 'backend/**'
```

`paths` 필터를 적용하여 백엔드 코드 변경이 없는 commit(문서, 매니페스트 등)에서는 워크플로우가 트리거되지 않도록 하였다.


### 2-3. flake8 설정 및 코드 수정 (backend/.flake8)

`.flake8` 설정 파일을 작성하였다. `max-line-length = 120`으로 설정하고 Black 스타일과 충돌하는 W503, E203을 ignore하였다. `__pycache__`, `migrations`, `htmlcov`, `.venv` 디렉터리를 제외 대상으로 지정하였다. 테스트 파일에는 `E501, S101`을 per-file-ignores로 처리하였다.

flake8 실행 결과 발견된 8개 오류를 수정하였다.

- `app/api/v1/bus.py`: datetime 미사용 import(F401) 3건 제거
- `app/core/redis.py`: `close_redis()`의 불필요한 `global redis_client` 선언(F824) 제거. 이 함수는 redis_client를 읽기만 하고 재할당하지 않으므로 global 선언이 불필요하다.
- `app/main.py`: 라우터 import의 E402(모듈 최상단 외 import) → `# noqa: E402` 처리. 순환 import 방지를 위해 의도적으로 하단에 배치된 구조이다.
- `app/models/boarding_record.py`: SQLAlchemy 순환참조 forward reference `"UserDevice | None"` F821 → `# noqa: F821` 처리
- `app/models/user_device.py`: 미사용 timezone import(F401) 제거, `"BoardingRecord"` forward reference F821 → `# noqa: F821` 처리

수정 후 `flake8 app/ --count --statistics` 결과 오류 0건 확인.


### 2-4. 파이프라인 설계 결정 사항

**PostgresDsn 타입 제약**: config.py의 `database_url` 필드가 `PostgresDsn` 타입으로 선언되어 있어 `sqlite+aiosqlite://` 스킴을 환경 변수로 전달하면 Pydantic 검증 오류가 발생한다. 테스트 시 실제 DB 쿼리는 conftest의 SQLite DI override로 처리되므로, CI 환경 변수에는 유효한 postgresql URL을 설정하는 방식을 택하였다.

**로컬 테스트**: ASGITransport가 FastAPI lifespan을 트리거하여 `init_db()`가 PostgreSQL 연결을 시도한다. 로컬 환경에서는 postgres/redis가 없으면 TCP 타임아웃이 발생하므로 `docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit`로 실행한다.

**ECR Secrets graceful skip**: Secrets가 없어도 lint/test/빌드는 정상 수행되도록 설계하였다. 이로써 ECR 없이도 PR 검증이 가능하다.


### 2-5. README 업데이트

`backend/README.md` 상단에 CI 배지와 파이프라인 구조 설명 섹션을 추가하였다. Job 순서를 ASCII 다이어그램으로 표현하고, 필요한 GitHub Secrets 3종을 표로 정리하였다.


## 3. 프로젝트 주차 진행 결과

파이프라인 구조 완성: lint → test → build-and-push의 3-Job 순차 실행 구조를 YAML로 구현하였다. YAML 문법 검증(`python3 -c "import yaml; yaml.safe_load(...)"`)을 통과하였다.

flake8 오류 0건: 8개 오류를 수정한 후 `flake8 app/ --count --statistics` 결과 오류 없음 확인.

pip 캐싱 적용: `actions/setup-python@v5`의 `cache: pip`와 `cache-dependency-path: backend/requirements.txt`로 의존성 캐싱을 활성화하여 반복 실행 시 빌드 시간을 단축하였다.

ECR 푸시 구현: `aws-actions/configure-aws-credentials@v4`, `aws-actions/amazon-ecr-login@v2` 공식 Action을 사용하여 main 브랜치 push 시 SHA 태그와 latest 태그로 ECR에 자동 푸시되도록 구성하였다.

GitHub Secrets 관리: AWS 인증 정보(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `ECR_REGISTRY`)를 코드에 하드코딩하지 않고 Secrets로 관리하는 패턴을 적용하였다.

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1


## 4. 기타 (문제점, 해결방법, 자기평가)

### 4-1. 문제점 및 해결방법

**PostgresDsn 타입이 SQLite URL을 거부**: CI 환경 변수로 `sqlite+aiosqlite:///:memory:`를 전달하면 Pydantic이 `URL scheme should be 'postgresql...'` 오류를 발생시켜 conftest import가 실패하였다. Settings의 `database_url`이 `PostgresDsn` 타입으로 선언되어 있고, `settings = get_settings()`가 모듈 import 시점에 즉시 평가되기 때문이다. 실제 테스트 쿼리는 conftest의 SQLite DI override로 처리되므로 CI 환경 변수를 유효한 postgresql URL로 변경하고, postgres 서비스를 다시 추가하여 해결하였다.

**로컬 pytest hang**: `AsyncClient(transport=ASGITransport(app=app))`이 FastAPI lifespan을 트리거하여 `init_db()`가 실행되고, 로컬에 postgres가 없을 때 asyncpg 연결 시도가 TCP 타임아웃(약 10분)까지 블로킹되었다. CI는 postgres 서비스가 올라가 있어 정상 동작하고, 로컬에서는 `docker-compose.test.yml`을 사용하도록 방향을 정리하였다.

**flake8 SQLAlchemy forward reference F821**: SQLAlchemy relationship에서 `"UserDevice | None"` 같은 문자열 형태의 forward reference를 flake8이 undefined name으로 오탐하였다. 실제 런타임에는 문자열로 평가되어 문제없으므로 `# noqa: F821` 주석으로 처리하였다.

### 4-2. 자기평가

GitHub Actions의 Job 의존성(`needs`), 서비스 컨테이너(`services`), Secrets 활용, conditional step(`if:` 조건)을 하나의 실제 파이프라인에서 모두 적용하면서 CI 구축의 전체 흐름을 체감하였다. 특히 코드에 민감 정보를 포함하지 않고 Secrets로 분리하는 패턴, 그리고 Secrets 미등록 시 graceful skip으로 개발 초기부터 배포 인프라 없이도 파이프라인을 사용할 수 있게 설계하는 방식이 인상적이었다.

아쉬운 점은 실제 GitHub Actions 상에서 워크플로우가 트리거되는 것을 직접 관찰하지 못한 것이다. 로컬 YAML 검증과 flake8 통과만 확인하였고, ECR 푸시는 실제 AWS 계정과 연동되지 않았다.
