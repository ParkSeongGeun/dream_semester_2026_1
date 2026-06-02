필수 목표
목표 (500자 이내)
14주차는 두 축으로 진행한다. 첫째, Jenkins를 도입하여 13주차 GitHub Actions와는 별개의 CI 파이프라인을 Pipeline as Code로 구축하고 두 도구를 비교 분석한다. 둘째, 그동안 로컬에서만 동작하던 백엔드를 AWS에 실제로 배포하고 iOS 앱을 클라우드 백엔드에 연동하여, iOS부터 임베디드와 백엔드, 데이터베이스까지 전 구간이 동작하는 실서비스 환경을 완성한다. 설정 파일 작성에 그치지 않고 Jenkins를 실제 기동하여 파이프라인이 SUCCESS로 완료되는 것과, AWS 인프라를 실제 생성하여 도메인으로 서비스가 응답하는 것까지 직접 검증하는 것을 핵심 목표로 한다.


필수 진행내용
진행내용 (500자 이내)
JCasC로 Jenkins 구성 전체를 코드화하고 Declarative Jenkinsfile로 Checkout, Lint, Test, Docker Build 단계를 구성하였다. 컨테이너를 실제 기동해 다섯 차례 디버깅 끝에 빌드를 SUCCESS시키고, git source 멀티브랜치와 SCM 폴링으로 push 자동 빌드를 확인하였다. 이어 Terraform 풀스택 48개 리소스를 실제 apply하여 VPC와 EC2, RDS, ALB, ACM, Route53을 생성하였다. EC2에 backend와 redis를 docker compose로 기동하고 RDS를 연결하였으며, production 테이블 생성을 위해 Alembic 마이그레이션을 도입하여 컨테이너 기동 시 자동 적용되게 하였다. iOS는 백엔드 주소를 클라우드 도메인으로 바꾸고 개발용 더미를 제거하였다.


필수 진행결과
진행결과 (500자 이내)
docker compose up 한 번으로 재현되는 Jenkins CI를 완성하고 빌드 다섯 번째가 전 단계 SUCCESS, pytest 77건 통과를 확인하였다. 멀티브랜치가 두 브랜치를 자동 빌드하고 폴링이 push를 감지해 자동 빌드하였다. AWS에서는 48개 리소스를 생성하여 도메인이 HTTPS로 응답하는 프로덕션을 구축하였다. 헬스체크에서 데이터베이스와 redis, 서울버스 API가 모두 정상이고 주변 정류장 35건과 실시간 도착정보를 확인하였다. 최종적으로 실기기와 ESP32로 iOS에서 강동01을 선택해 BLE 매칭과 알림 전송이 성공하고 탑승 기록이 RDS에 정확히 저장되는 전 구간을 검증하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
Jenkins에서는 timestamper 미설치, ARM64 wheel 부재, dockerignore의 tests 제외, buildx 누락을 차례로 해결하였다. 배포에서는 EC2 볼륨 크기, user-data 템플릿 이스케이프, production 테이블 부재, requirements.prod의 alembic 누락, iOS 기기명 한글 영문 불일치를 해결하였다. compose 설치 실패와 alembic 누락은 dev와 prod 의존성 이중관리에서 비롯된 12주차와 동일한 패턴이었다. 자기평가로는 self-hosted CI의 책임 범위를 체감하고, Terraform 실배포로 인프라와 애플리케이션 경계의 문제를 직접 해결하였으며, CI/CD부터 클라우드 배포와 iOS 연동까지 전체 흐름을 한 주차에 통합하여 완성한 점이 의미 있었다.
