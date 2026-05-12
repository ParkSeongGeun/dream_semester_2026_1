필수 목표
목표 (500자 이내)
11주차는 두 축으로 진행하였다. 첫째, 10주차 minikube K8s 환경에서 iPhone 실기기까지 통신 라인을 확장하여 iOS ↔ 백엔드 ↔ ESP32 BLE 풀스택 통신을 검증하고 readinessProbe 외부 API 누수·init_db 모델 등록 누락의 두 가지 결함을 수정한다. 둘째, AWS EKS 기반 프로덕션 인프라를 Terraform 으로 코드화하고 kustomize base/overlays 구조로 dev/prod 네임스페이스를 분리하며 HPA(CPU 70%), PV/PVC, nginx-ingress 를 minikube 에서 실제로 검증한다.


필수 진행내용
진행내용 (500자 이내)
iOS Info.plist 에 NSLocalNetworkUsageDescription·NSBonjourServices 를 추가해 실기기 LAN 통신을 허용하였다. init_db 에 side-effect import 와 environment 가드를 추가하고 /api/v1/health/ready 를 신설하여 readinessProbe 에서 외부 API 를 제거하였다. Terraform modules/eks 를 신설(클러스터·노드 그룹·IAM)하고 environments/dev 에 연결하였다. infra/k8s/base 에 deployment·service·configmap·hpa·pvc 를 두고 overlays/dev|prod 에 namespace·ResourceQuota·Ingress·패치를 작성하였다. minikube 에서 metrics-server 활성화, HPA 적용, Helm 으로 nginx-ingress 설치, Ingress 연결을 순서대로 실행하였다.


필수 진행결과
진행결과 (500자 이내)
iPhone 실기기에서 GET /api/v1/bus/stations(200 OK) → BLE 알림 송신(BF_DREAM_143 매칭 성공) → POST /api/v1/boarding/record(201, DB 저장) 풀스택 흐름을 한 번의 사용자 동작으로 통과시켰다. /api/v1/health/ready 분리로 파드 3개 기준 분당 18회였던 서울 TOPIS 호출이 0회로 줄었다. terraform validate 성공, kubectl kustomize dry-run dev/prod 양쪽 통과, comfortablemove-dev 네임스페이스·ResourceQuota 실적용을 확인하였다. HPA 부하 테스트에서 CPU 228%/70% 감지 시 replicas 3→5 자동 스케일아웃을 실시간으로 관찰하였다. nginx-ingress 1/1 Running, Ingress host dev.api.comfortablemove.com 연결도 확인하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
문제점·해결: iOS -1009 로컬 네트워크 거부 → NSLocalNetworkUsageDescription 추가. relation 'users_devices' not exist → init_db side-effect import + environment 가드. readinessProbe 일일 한도 5분 소진 → /health/ready 분리. minikube image 캐시 미갱신 → eval $(minikube docker-env) 내부 빌드. Docker daemon 응답 불가 → osascript+pkill 강제 재시작. EKS dev NAT 비활성 충돌 → 실 프로비저닝 시 퍼블릭 서브넷 배치 또는 VPC Endpoint 로 해결 예정.
자기평가: HPA 스케일아웃을 직접 관찰하며 K8s 선언적 자동 스케일링을 체화하였다. readinessProbe 분리 패턴은 probe 주기×replicas×외부 API 호출의 곱이 한도를 소진한다는 인프라 레이어 단일 책임 원칙의 실제 사례였다. 아쉬운 점은 terraform apply 실 EKS 프로비저닝 미완과 iOS BLE hack 미복구이다.
