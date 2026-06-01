필수 목표
목표 (500자 이내)
Jenkins를 Docker로 설치하고 맘편한 이동 백엔드의 CI 파이프라인을 구축한다. Pipeline as Code 개념을 학습하고 Jenkinsfile 작성법을 익히며 선언적과 스크립트 파이프라인의 차이를 이해한다. 파이프라인 단계는 Checkout, Lint, Test, Docker Build, Push to ECR로 구성한다. 13주차에 구축한 GitHub Actions와 동일한 단계를 Jenkins로 재구현하여 두 도구의 차이를 비교 분석한다. 설정 파일 작성에 그치지 않고 Jenkins를 실제로 기동하여 파이프라인이 SUCCESS로 완료되는 것을 검증하는 것을 핵심 목표로 한다.


필수 진행내용
진행내용 (500자 이내)
Pipeline as Code 정신에 맞춰 JCasC로 Jenkins 구성 전체를 코드화하였다. Dockerfile에 Python과 Docker CLI, buildx, 플러그인을 사전 설치하고 casc.yaml에 관리자 계정과 파이프라인 Job을 정의하여 Setup Wizard 없이 재현되게 하였다. 루트에 Declarative Jenkinsfile을 작성하였다. Lint는 노드 venv에서 flake8로 수행하고, Test는 python 공식 이미지 기반 Dockerfile.test를 빌드해 컨테이너 안에서 pytest를 실행한다. docker.sock을 마운트하여 컨테이너에서 host Docker로 이미지를 빌드한다. REST API로 파이프라인을 트리거하며 SUCCESS까지 다섯 차례 디버깅하였다.


필수 진행결과
진행결과 (500자 이내)
docker compose up 한 번으로 관리자 계정과 플러그인, 파이프라인 Job이 자동 구성되는 재현 가능한 CI 환경을 완성하였다. 빌드 5회차가 Checkout, Lint, Test, Docker Build 전 단계를 통과하여 SUCCESS로 완료되었다. pytest 77건 통과와 운영 이미지 빌드 성공을 콘솔 로그와 JUnit 리포트로 확인하였다. ECR 자격증명이 없어도 lint와 test, 빌드가 정상 수행되도록 graceful skip을 적용하였다. GitHub Actions와 Jenkins의 장단점을 실제 코드 기준으로 비교한 문서를 작성하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
timestamper 미설치로 timestamps 옵션이 실패하여 제거하였다. ARM64 노드에서 asyncpg와 pydantic-core가 컴파일에 실패하여, 테스트와 빌드를 공식 python 이미지 기반 Docker로 전환해 wheel이 제공되는 환경에서 빌드되게 하였다. 운영용 dockerignore가 tests를 제외하여 테스트 이미지 빌드가 실패하였고, BuildKit의 파일별 ignore 기능으로 테스트 전용 ignore를 분리해 해결하였다. Jenkins 컨테이너에 buildx가 없어 다시 실패하여 buildx 플러그인을 설치하였다. 자기평가: 설치를 넘어 실제 기동과 SUCCESS 검증까지 수행하며 self-hosted CI의 책임 범위를 체감하였다.
