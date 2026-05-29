필수 목표
목표 (500자 이내)
GitHub Actions를 활용하여 맘편한 이동 백엔드의 CI 파이프라인을 구축한다. Workflow, Job, Step, Runner, Event 개념을 학습하고 YAML로 워크플로우 파일을 작성하는 방법을 익힌다. 파이프라인 단계는 코드 체크아웃, Python 환경 설정, 의존성 설치, 린트(flake8), 테스트(pytest), Docker 이미지 빌드, ECR 푸시로 구성하며 push와 pull_request 이벤트를 트리거로 설정한다. GitHub Secrets로 AWS 인증 정보를 관리하고 의존성 캐싱으로 빌드 시간을 단축한다.


필수 진행내용
진행내용 (500자 이내)
ci.yml을 lint, test, build-and-push 3-Job 구조로 재구성하였다. lint Job은 flake8로 정적 분석을 수행하고, test Job은 postgres와 redis 서비스를 띄워 pytest를 실행하며 pip cache로 의존성 캐싱을 적용하였다. build-and-push Job은 Docker 이미지를 항상 빌드하고 ECR Secrets 등록 시 main 브랜치 push에서만 SHA 태그와 latest 태그로 ECR에 푸시한다. backend/.flake8 설정 파일을 작성하고 미사용 import, 불필요한 global 선언 등 8개 오류를 수정하여 0건을 달성하였다. README에 CI 배지와 파이프라인 다이어그램을 추가하였다.


필수 진행결과
진행결과 (500자 이내)
lint, test, build-and-push 3-Job 파이프라인이 YAML 문법 검증을 통과하였다. flake8 오류 0건을 확인하였다. pip cache 적용으로 반복 실행 시 의존성 설치 시간이 단축된다. ECR 푸시는 aws-actions 공식 Action을 사용하고 Secrets 미등록 시 warning으로 건너뛰어 인프라 없이도 파이프라인이 정상 동작한다. backend 경로 변경 시에만 워크플로우가 트리거되도록 paths 필터를 적용하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
PostgresDsn 타입이 sqlite URL을 거부하여 CI 환경 변수를 postgresql URL로 변경하고 postgres 서비스를 복원하였다. 로컬에서 ASGITransport가 lifespan을 트리거하여 postgres 연결 시도가 TCP 타임아웃까지 블로킹되었고 docker-compose.test.yml 사용으로 방향을 정리하였다. SQLAlchemy forward reference가 flake8 F821 오탐을 일으켜 noqa 처리하였다. 자기평가: Job 의존성, 서비스 컨테이너, Secrets, conditional step을 실제 파이프라인에서 적용하며 CI 구축 흐름 전반을 체감하였다.
