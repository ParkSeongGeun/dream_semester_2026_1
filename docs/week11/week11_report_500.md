필수 목표
목표 (500자 이내)
11주차는 두 축으로 진행하였다. 첫째, 10주차 minikube K8s 환경에서 iPhone 실기기까지 통신 라인을 확장하여 iOS, 백엔드, ESP32 BLE 풀스택 통신을 검증하고 readinessProbe 외부 API 누수와 init_db 모델 등록 누락의 두 가지 결함을 수정한다. 둘째, AWS EKS 기반 프로덕션 인프라를 Terraform 으로 코드화하고 kustomize base/overlays 구조로 dev/prod 네임스페이스를 분리하며 HPA(CPU 70%), PV/PVC, nginx-ingress 를 minikube 에서 실제로 검증한다.


필수 진행내용
진행내용 (500자 이내)
iOS Info.plist 에 NSLocalNetworkUsageDescription 과 NSBonjourServices 를 추가해 실기기 LAN 통신을 허용하였다. init_db 에 side-effect import 와 environment 가드를 추가하고 /api/v1/health/ready 를 신설하여 readinessProbe 에서 외부 API 를 제거하였다. Terraform modules/eks 를 신설(클러스터, 노드 그룹, IAM)하고 environments/dev 에 연결하였다. infra/k8s/base 에 deployment, service, configmap, hpa, pvc 를 두고 overlays/dev, prod 에 namespace, ResourceQuota, Ingress, 패치를 작성하였다. minikube 에서 metrics-server 활성화, HPA 적용, nginx-ingress 설치, Ingress 연결을 실행하였다.


필수 진행결과
진행결과 (500자 이내)
iPhone 실기기에서 버스 도착정보 조회, BLE 알림 송신(BF_DREAM_143 매칭 성공), POST /api/v1/boarding/record 201 및 DB 저장까지 풀스택 흐름을 한 번의 사용자 동작으로 통과시켰다. /api/v1/health/ready 분리로 파드 3개 기준 분당 18회였던 서울 TOPIS 호출이 0회로 줄었다. terraform validate 성공, kubectl kustomize dry-run dev/prod 양쪽 통과, comfortablemove-dev 네임스페이스와 ResourceQuota 실적용을 확인하였다. HPA 부하 테스트에서 CPU 228% 감지 시 replicas 가 3에서 5로 자동 스케일아웃됨을 관찰하였고 nginx-ingress 와 Ingress 연결도 확인하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
iOS 실기기에서 첫 LAN 요청이 거부된 것은 iOS 14 이상에서 로컬 네트워크 권한이 별도로 필요하다는 점을 놓쳤기 때문이며 NSLocalNetworkUsageDescription 을 추가하여 해결하였다. readinessProbe 가 외부 API 를 10초마다 호출하여 파드 3개 기준 분당 18회씩 일일 한도를 소진하는 문제는 /health/ready 분리로 차단하였다. minikube 이미지 캐시 미갱신은 minikube 내부 docker 에서 직접 빌드하는 방식으로 우회하였다.
자기평가: HPA 스케일아웃을 직접 관찰하며 선언적 자동 스케일링을 체화하였다. probe 주기와 replicas 수가 외부 API 한도 소진에 미치는 영향을 수치로 확인하면서 인프라 레이어에서도 단일 책임 원칙이 중요함을 깨달았다. 아쉬운 점은 실 EKS 프로비저닝 미완과 iOS BLE hack 미복구이다.
