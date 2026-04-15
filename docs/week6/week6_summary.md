목표
AWS 핵심 서비스(IAM, VPC, EC2)를 학습하고 맘편한 이동 백엔드를 위한 클라우드 인프라를 구성하는 것을 목표로 한다. IAM으로 최소 권한 원칙에 따라 프로젝트 전용 그룹과 사용자를 생성하고, 리전 조건으로 권한 범위를 제한한다. VPC를 서울 리전 2개 가용영역에 퍼블릭/프라이빗 서브넷으로 설계하고, 인터넷 게이트웨이와 NAT 게이트웨이로 라우팅을 구성한다. EC2 인스턴스를 생성하고 보안 그룹으로 SSH(22)와 API(8000) 포트만 현재 IP에서 접근 가능하도록 제한한다. User Data 스크립트로 Docker와 Docker Compose를 자동 설치하고, EC2에서 맘편한 이동 백엔드가 정상 동작하는 것을 확인한다. AWS Budgets로 월간 비용 알림을 설정하여 프리티어 초과를 방지한다. 5주차 지도교수 피드백을 반영하여 GitHub Actions CI/CD 파이프라인을 구축하고, 모든 자격증명을 GitHub Secrets로 관리하는 체계를 수립한다.

진행내용
IAM 커스텀 정책 2개(EC2/VPC 관리, 비용 조회)를 최소 권한 원칙에 따라 작성하고, 그룹과 사용자를 생성하는 AWS CLI 자동화 스크립트를 작성하였다. VPC(10.0.0.0/16)를 2개 가용영역에 퍼블릭 서브넷 2개, 프라이빗 서브넷 2개로 설계하고 인터넷 게이트웨이와 NAT 게이트웨이를 연결하는 CLI 스크립트를 작성하였다. EC2 보안 그룹에서 SSH(22)와 API(8000) 포트를 현재 IP에서만 허용하고, t2.micro 인스턴스를 생성하는 스크립트를 작성하였다. User Data로 Docker, Docker Compose 설치와 SSH 보안을 자동화하였다. 월 $10 예산에 4단계 알림을 설정하는 Budget 스크립트를 작성하였다. GitHub Actions CI로 PR 시 자동 테스트와 Docker 빌드 검증을, CD로 main 병합 시 EC2 자동 배포를 구성하였다. 지도교수 피드백을 반영하여 자격증명을 GitHub Secrets로 관리하였다.

진행결과
EC2에서 docker compose up -d 실행 후 backend, postgres, redis 3개 컨테이너가 모두 healthy 상태로 기동됨을 확인하였다. 헬스체크 API에서 database connected, redis connected, seoul_bus_api reachable 응답을 확인하여 로컬 환경과 동일하게 EC2에서도 정상 동작함을 검증하였다. AWS 인프라 스크립트 7개(IAM 정책 2개, setup-iam.sh, setup-vpc.sh, setup-ec2.sh, user-data.sh, setup-budget-alarm.sh)와 GitHub Actions 워크플로우 2개(ci.yml, cd.yml)를 작성하였다. 보안 그룹은 현재 IP(/32)에서만 접근을 허용하여 포트 노출을 방지하였다. CI에서 PR 시 자동 테스트, CD에서 main 병합 시 EC2 배포를 검증하였다. 총 9개 파일을 7개 커밋으로 GitHub에 반영하였다.

기타
(문제점, 해결방법, 자기평가 등)
가장 큰 성과는 모든 인프라를 AWS CLI 스크립트로 자동화하여 재현 가능성을 확보한 점이다. 콘솔 클릭 대신 CLI 스크립트로 작성하여 Git으로 인프라 변경 이력을 추적할 수 있다. IAM에서 AdministratorAccess 대신 커스텀 정책으로 필요한 액션만 허용하고 리전을 제한하여 Access Key 유출 시 피해를 최소화하였다. 보안 그룹에서 0.0.0.0/0 대신 현재 IP(/32)로 인바운드를 제한하는 중요성을 학습하였다. 지도교수 피드백을 반영하여 .gitignore 등록, GitHub Secrets 활용 등 다층적 보안 체계를 수립하였다. NAT 게이트웨이가 프리티어에 미포함되어 시간당 과금이 발생하는 문제를 발견하고, 학습 후 삭제하여 비용을 절감하였다. 아쉬운 점은 도메인 연결과 HTTPS를 아직 완료하지 못한 점이며, 다음 주차에는 Terraform 전환과 ALB 도입을 계획하고 있다.
