1. 프로젝트 주차 목표

11주차는 두 가지 축으로 구성되었다. 첫 번째 축은 10주차에 구축한 K8s 학습 환경(minikube + 백엔드 Deployment 3 replicas)에서 iPhone 실기기까지 통신 라인을 확장하여 iOS ↔ 백엔드 ↔ ESP32 BLE 하드웨어의 풀스택 통신을 직접 검증하는 것이다. 동시에 10주차 이후 드러난 두 가지 결함—K8s readinessProbe 가 health endpoint 의 외부 API 호출을 트리거하여 서울 TOPIS 일일 한도(100 회) 가 5 분 만에 소진되는 누수, 그리고 백엔드 init_db 가 모델 모듈을 import 하지 않아 boarding_records/users_devices 테이블이 자동 생성되지 않는 누락—을 수정하여 백엔드의 데이터 수집 파이프라인을 정상화한다.

두 번째 축은 AWS EKS 기반 프로덕션 인프라 코드를 작성하고 minikube 에서 실제로 구동하는 것이다. 기존 9주차 Terraform 구조(modules/ + environments/dev|prod)에 EKS 모듈을 추가하고, K8s 매니페스트를 kustomize base/overlays 구조로 재편하여 dev/prod 네임스페이스 분리, HPA, PV/PVC, nginx-ingress 를 포함한 EKS 배포 준비 상태를 완성하고 minikube 에서 검증한다.


2. 프로젝트 주차 진행 내용

2-1. 10주차 환경 재기동 및 Docker daemon 복구

세션 시작 시점에 Docker daemon 이 응답 불가 상태였다. docker info / docker ps 모두 timeout 으로 응답이 없었고 minikube start 가 PROVIDER_DOCKER_NOT_RUNNING 으로 실패하였다. osascript quit + pkill 로 Docker Desktop 을 강제 종료한 후 open -a Docker 로 재시작하였고, until 폴링으로 daemon ServerVersion 응답 여부를 감지하는 방식으로 ready 시점을 정확히 파악하였다.

2-2. minikube 재구축

기존 minikube 컨테이너는 host: Running 이지만 kubelet 이 "activating (auto-restart, Result: exit-code)" 상태로 494 회째 재시작 루프에 빠져 있었다. journalctl -u kubelet 으로 "failed to run Kubelet: unable to load bootstrap kubeconfig: /etc/kubernetes/bootstrap-kubelet.conf: no such file" 를 확인하였고, minikube delete 후 재생성하는 방식으로 깨끗하게 회복하였다. 컨테이너 안의 K8s 부트스트랩 파일이 손상된 케이스로, 재시작만으로는 복구가 안 되고 컨테이너 자체를 재생성해야 한다는 점을 학습하였다.

2-3. iOS 실기기 통신 라인 구축

실기기는 시뮬레이터와 달리 localhost 를 못 쓰므로 Mac LAN IP(172.30.1.79) 로 백엔드를 노출해야 하였다. kubectl port-forward 의 기본값이 127.0.0.1 only 이므로 --address 0.0.0.0 옵션으로 모든 인터페이스에 listen 시켰다. iOS Config.xcconfig 의 BACKEND_BASE_URL 을 LAN IP 로 변경하였다.

첫 호출 시 NSURLErrorDomain Code=-1009 "Local network prohibited" 에러가 발생하였다. iOS 14+ 의 로컬 네트워크 권한이 별도이고 NSAllowsArbitraryLoads 만으로는 부족하다는 점을 확인하였다. Info.plist 에 NSLocalNetworkUsageDescription 과 NSBonjourServices(_http._tcp) 를 추가하였고, 첫 호출 시 권한 다이얼로그 → 허용 후 통신이 정상화되었다.

2-4. 백엔드 init_db 모델 등록 누락 fix

iOS BLE 결과를 백엔드에 POST 했을 때 "relation 'users_devices' does not exist" 에러가 발생하였다. backend/app/db/session.py 의 init_db 가 Base.metadata.create_all 을 호출하지만 모델 모듈(app.models.user_device, boarding_record) 을 import 하지 않아 metadata 에 테이블이 등록되지 않은 상태였다. 또한 if settings.debug 가드로 인해 ConfigMap 의 DEBUG="false" 환경에서는 create_all 자체가 호출되지 않고 있었다.

session.py 의 init_db 안에 from app.models import user_device, boarding_record (side-effect import) 를 추가하고, 가드를 settings.environment in ("development", "testing") 로 변경하였다. 학습 환경 일관성을 위해 ConfigMap 의 ENVIRONMENT 도 "production" → "development" 로 변경하였다.

2-5. readinessProbe 외부 API 트래픽 누수 차단

실기기 테스트 중 도착정보 API 가 "인증모듈 에러코드(22): LIMITED NUMBER OF SERVICE REQUESTS EXCEEDS" 로 거부되었다. 일일 100 회 한도가 짧은 시간 안에 소진된 원인을 추적한 결과, K8s readinessProbe 가 /api/v1/health 를 10 초 주기로 호출하고 health endpoint 가 seoul_bus_service.check_api_health() 로 외부 API 를 직접 호출하는 구조였다. 파드 3 개 × 6 회/분 = 18 회/분 → 일일 한도가 약 5~6 분 만에 도달하는 계산이다.

해결로 /api/v1/health/ready 엔드포인트를 신설하여 DB·Redis 만 확인하고 외부 API 호출은 하지 않도록 분리하였다. infra/k8s/deployment.yaml 의 readinessProbe.httpGet.path 를 /api/v1/health/ready 로 교체하였다. /api/v1/health 는 수동/모니터링용으로 외부 API 까지 검증하는 기존 동작을 유지하였다.

2-6. 풀스택 통신 검증

실기기에서 알림 버튼을 두 번(소리 ON/OFF 각 1 회) 누른 후 K8s 백엔드 파드 로그에 "POST /api/v1/boarding/record HTTP/1.1" 201 이 두 번 기록되었고, boarding_records 테이블에 동일한 device_id 의 두 행(route_name=143, bus_device_id=BF_DREAM_143, station_name=한산중학교, sound_enabled=t/f, notification_status=success) 이 존재하였다. users_devices 테이블에는 해당 device_id 가 자동 등록되었고 last_active_at 이 두 번째 호출 시점으로 갱신되었다(upsert 로직 정상 동작).

2-7. Terraform EKS 모듈 추가

9주차에 구성한 infra/terraform/modules/ 구조에 eks 모듈을 신설하였다. 모듈 구성은 다음과 같다. IAM 역할로 EKS 컨트롤 플레인(AmazonEKSClusterPolicy)과 노드 그룹(AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, AmazonEC2ContainerRegistryReadOnly) 역할을 각각 생성한다. aws_eks_cluster 로 컨트롤 플레인을 퍼블릭+프라이빗 서브넷에 배치하고 엔드포인트 퍼블릭 접근을 활성화하여 로컬 kubectl 접근을 허용한다. aws_eks_node_group 으로 관리형 노드 그룹을 프라이빗 서브넷에 배치하며 maxUnavailable=1 롤링 업데이트를 적용한다.

environments/dev/main.tf 에 module "eks" 블록을 추가하고 변수 5 개(kubernetes_version, node_instance_types, node_desired/min/max_size) 를 dev/variables.tf 에 정의하였다. terraform init -upgrade 후 terraform validate 로 구문 검증을 통과하였다.

2-8. K8s 매니페스트 kustomize base/overlays 구조 재편

기존 infra/k8s/ 의 단일 환경 구조(minikube 전용) 를 유지하면서 EKS 배포용 base/overlays 구조를 병행 추가하였다.

infra/k8s/base/ 에는 환경 공통 리소스를 두었다. deployment.yaml 은 hostAliases 제거(EKS 는 RDS DNS 직접 사용), imagePullPolicy=Always, replicas=2 로 구성하였다. hpa.yaml 은 autoscaling/v2 API 를 사용하며 CPU 70% 임계값에 minReplicas=2, maxReplicas=5 를 지정하였다. pvc.yaml 은 StorageClass gp2, 1Gi ReadWriteOnce 로 정의하였다.

infra/k8s/overlays/dev/ 에는 comfortablemove-dev 네임스페이스, ResourceQuota(CPU 1/2, 메모리 1Gi/2Gi, 파드 10 개), host=dev.api.comfortablemove.com Ingress, replicas=1·HPA minReplicas=1 패치를 두었다. infra/k8s/overlays/prod/ 에는 comfortablemove-prod 네임스페이스, ResourceQuota(CPU 2/4, 메모리 2Gi/4Gi, 파드 20 개), host=api.comfortablemove.com Ingress(TLS 주석)를 두었다.

kubectl kustomize overlays/dev 와 kubectl kustomize overlays/prod 로 dry-run 렌더링을 검증하였다.

2-9. nginx-ingress Helm 설치 및 Ingress 동작 확인

minikube 에서 Helm 으로 nginx-ingress-controller 를 설치하고 실제 동작을 검증하였다.

```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=NodePort
```

설치 후 ingress-nginx-controller 파드가 1/1 Running 상태로 기동하였고 NodePort 30535(HTTP), 30361(HTTPS) 로 노출되었다. overlays/dev/ingress.yaml 을 comfortablemove 네임스페이스에 적용하여 host=dev.api.comfortablemove.com, ADDRESS=10.99.206.7 로 매핑됨을 kubectl get ingress 로 확인하였다.

2-10. HPA 실제 스케일아웃·스케일인 검증

metrics-server 애드온을 활성화한 후 HPA 를 comfortablemove 네임스페이스에 적용하고 busybox 부하 발생기 3 개를 투입하였다. /api/v1/health/ready 와 /api/v1/bus/arrivals 를 무한 루프로 호출하여 CPU 를 228% 까지 올렸다. HPA 가 70% 임계값을 감지하여 replicas 를 3 → 5(maxReplicas) 로 자동 증가시켰고, kubectl top pods 로 파드별 CPU 214~249m 사용을 확인하였다. 부하 발생기 삭제 후 안정화 기간(기본 5분) 이후 minReplicas=2 로 수렴하는 스케일인이 예정되었다.


3. 프로젝트 주차 진행 결과

실기기 풀스택 통신 검증: iPhone 실기기에서 GET /api/v1/bus/stations(200 OK), BLE 알림 송신(BF_DREAM_143 → "✅ 데이터 전송 성공"), POST /api/v1/boarding/record(HTTP 201, DB 저장 확인) 의 전체 흐름이 한 번의 사용자 동작으로 통과하였다.

백엔드 데이터 파이프라인 정상화: init_db 의 모델 import 누락과 environment 가드를 수정하여 boarding_records / users_devices 테이블이 컨테이너 첫 기동 시 자동 생성되도록 하였다. readinessProbe 를 /api/v1/health/ready 로 분리하여 파드 3 개 기준 분당 18 회였던 외부 API 호출이 0 회로 줄었다.

EKS 인프라 코드 완성 및 minikube 검증: Terraform EKS 모듈이 terraform validate 를 통과하였고, kustomize base/overlays 구조가 dev/prod 양쪽에서 dry-run 을 통과하였다. minikube 에서 Namespace, ResourceQuota, nginx-ingress(Helm), Ingress, HPA 를 실제로 적용하였다. 특히 HPA 는 CPU 228%/70% 감지 시 replicas 3→5 자동 스케일아웃을 실시간으로 확인하였다.

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1
iOS: https://github.com/BFDream-AutoEver/BFDream-iOS


4. 기타(문제점, 해결방법, 자기평가 등)

4-1. 문제점 및 해결방법

서울 TOPIS API 일일 100 회 한도가 readinessProbe 에 의해 5~6 분 만에 소진되는 누수를 발견하였다. K8s health endpoint 가 외부 의존성을 한 곳에 모두 검증하는 단일 패턴이었지만, probe 가 분당 다회 호출하는 구조와 결합되면 외부 API 한도가 무의식적으로 빠르게 소진된다. /health/ready(probe 전용) 와 /health(수동/모니터링) 를 분리하는 패턴으로 해결하였다.

iOS 14+ 로컬 네트워크 권한 누락으로 -1009 에러가 발생하였다. NSAllowsArbitraryLoads 만으로는 LAN 통신이 허용되지 않으며 NSLocalNetworkUsageDescription 별도 추가가 필요하다는 점을 학습하였다.

minikube image 캐시 문제로 호스트에서 빌드한 새 이미지가 minikube 안에 반영되지 않았다. 같은 태그(:dev) + IfNotPresent 조합에서 발생하는 함정이며, eval $(minikube docker-env) 로 minikube 내부 docker 컨텍스트에서 직접 빌드하는 방식으로 우회하였다.

EKS dev 환경에서 NAT Gateway 비활성 문제가 있다. 프라이빗 서브넷 노드는 ECR 이미지 pull 을 위해 인터넷 접근이 필요한데 dev 는 비용 절감을 위해 NAT 를 끈다. 퍼블릭 서브넷에 노드 배치 또는 VPC Endpoint 추가로 해결 가능하며 실제 EKS 프로비저닝 시 결정하기로 하였다.

4-2. 자기평가

가장 큰 성과는 iPhone 실기기에서 iOS ↔ 백엔드 ↔ ESP32 의 풀스택 통신을 한 번의 사용자 동작으로 검증한 점이다. LAN 노출/로컬 네트워크 권한/BLE 매칭/DB 저장의 네 가지를 한꺼번에 통과시키면서 풀스택 시스템이 끊기는 지점을 직접 체감하였다.

EKS 인프라 코드와 minikube 실검증도 의미 있는 성과이다. kustomize base/overlays 로 네임스페이스 분리·HPA·PV/PVC·Ingress 를 한 번에 정의하는 구조를 체화하였다. HPA 스케일아웃(CPU 228% → replicas 5)을 직접 관찰하면서 K8s 의 선언적 자동 스케일링이 실제로 어떻게 동작하는지 체감하였다. nginx-ingress 를 Helm 으로 설치하고 도메인 기반 Ingress 를 연결하는 절차도 실습하였다.

아쉬운 점은 실제 AWS 계정에 EKS 를 프로비저닝하고 terraform apply 의 전체 결과를 확인하지 못한 점이다. iOS 임시 hack(mock 143 도착정보 + BLE 송신 번호 고정) 제거와 통계 API iOS 화면 구현도 다음 주차로 이연하였다.
