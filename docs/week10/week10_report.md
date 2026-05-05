1. 프로젝트 주차 목표
10주차에는 Kubernetes의 핵심 개념을 학습하고 로컬 클러스터에 맘편한 이동(ComfortableMove) 백엔드 API를 직접 배포하는 것을 목표로 한다. Control Plane(API Server, etcd, Scheduler, Controller Manager)과 Worker Node(kubelet, kube-proxy, Container Runtime)의 역할을 이해하고, Pod, ReplicaSet, Deployment, Service, ConfigMap, Secret 오브젝트의 책임과 상호 관계를 학습한다. Minikube로 로컬 Kubernetes v1.34.0 클러스터를 구성하고, 백엔드 API를 Deployment(replicas=3)로 배포하여 셀프힐링과 롤링 업데이트를 직접 검증한다. 매니페스트는 infra/k8s/ 디렉토리에 Namespace, ConfigMap, Secret(템플릿), Deployment, Service, kustomization.yaml, README의 형태로 정리하고, 실제 시크릿 값이 들어간 secret.yaml은 .gitignore로 커밋을 차단한다. 부수 작업으로 9주차에 작성한 iOS-백엔드 통합 코드 중 누락되었던 device_id 관리와 배려석 알림 결과 기록 호출(POST /api/v1/boarding/record)을 iOS 측에 추가하고, 백엔드의 미등록 device_id 자동 등록(FK 위반 방지) 로직을 보강한다. 또한 그동안 누적된 GitHub Actions CI/CD 워크플로의 실패(시크릿 미등록, ENVIRONMENT Literal 불일치, Redis 모킹 회귀, aiosqlite 의존성 누락)를 정리하여 매 push마다 안정적으로 워크플로가 통과하도록 워크플로와 테스트 인프라를 손본다.


2. 프로젝트 주차 진행 내용

2-1. Kubernetes 핵심 개념 정리
Kubernetes 아키텍처를 학습하면서 Control Plane은 클러스터 전체의 desired state를 관리하고 Worker Node는 실제 컨테이너 런타임을 호스팅한다는 책임 분리를 파악하였다. Control Plane의 API Server는 모든 컴포넌트가 통신하는 단일 진입점이고, etcd는 클러스터 상태를 저장하는 분산 KV 저장소이며, Scheduler는 신규 Pod의 배치 노드를 결정하고 Controller Manager는 ReplicaSet/Deployment 등 컨트롤러 루프를 실행한다. Worker Node의 kubelet은 노드별 Pod 라이프사이클을 관리하고, kube-proxy는 Service의 가상 IP를 iptables/ipvs 규칙으로 노드에 적용하며, Container Runtime(containerd 등)이 실제 컨테이너를 띄운다는 흐름을 학습하였다.

오브젝트 단계에서는 Pod가 가장 작은 배포 단위(공유 네트워크/스토리지를 가진 컨테이너 묶음)이고, ReplicaSet이 Pod 사본 수를 보장하며, Deployment가 ReplicaSet을 관리하면서 롤링 업데이트와 롤백을 제공한다는 계층을 파악하였다. Service는 Pod IP의 변동성을 추상화하여 안정적인 가상 IP/DNS를 제공하고, ConfigMap은 비민감 환경변수, Secret은 민감 값을 분리 저장한다는 분담을 학습하였다. 이번 주차의 매니페스트 작성은 이 분담을 그대로 반영하였다.

2-2. Minikube 로컬 클러스터 구성
macOS(arm64) 환경에서 minikube v1.37.0을 docker driver로 기동하였다. 기존 클러스터가 v1.34.0으로 남아있어 v1.31.0으로의 다운그레이드가 거부되었고, kubectl client(v1.34.1)와의 호환을 위해 동일 버전(v1.34.0)으로 재기동하였다. 노드는 Ready 상태로 올라왔으며 kubectl cluster-info로 control plane(127.0.0.1:58209)과 CoreDNS의 정상 응답을 확인하였다. driver는 docker, CNI는 bridge, 추가 addon은 storage-provisioner와 default-storageclass만 활성화한 최소 구성이다.

2-3. K8s 매니페스트 작성 (infra/k8s/)
infra/k8s/ 디렉토리에 다음 7개 파일을 작성하였다. namespace.yaml은 comfortablemove 네임스페이스를 정의하여 모든 리소스를 격리한다. configmap.yaml은 ENVIRONMENT, DEBUG, HOST, PORT, LOG_LEVEL, DB_ECHO, DB_POOL_SIZE, DB_MAX_OVERFLOW, REDIS_TTL_*, SEOUL_BUS_API_BASE_URL/TIMEOUT/MAX_RETRIES, CORS_* 등 비민감 환경변수만 담는다. secret.example.yaml은 DATABASE_URL, REDIS_URL, SEOUL_BUS_API_KEY, SECRET_KEY 4개의 키를 CHANGE_ME 플레이스홀더로 채운 템플릿이며, 실제 값을 채운 secret.yaml은 infra/k8s/.gitignore로 커밋이 차단된다.

deployment.yaml은 replicas=3, RollingUpdate(maxSurge=1, maxUnavailable=0), envFrom으로 ConfigMap+Secret을 모두 주입, livenessProbe(/), readinessProbe(/api/v1/health), resources(requests cpu 100m memory 128Mi, limits cpu 500m memory 512Mi)를 포함한다. service.yaml은 ClusterIP type으로 80→8000 포트 매핑을 구성한다. kustomization.yaml은 5개 리소스를 단일 진입점으로 묶어 kubectl apply -k infra/k8s/ 한 번으로 전체 배포가 가능하도록 하였다. README.md에는 사전 준비, 배포 절차, 검증 체크리스트, 정리 명령을 정리하였다.

2-4. 백엔드 이미지 빌드 및 minikube 로드
backend/Dockerfile(Stage 1: Python 3.12-slim builder, Stage 2: non-root runtime, gunicorn+uvicorn worker 2개, port 8000, /api/v1/health 헬스체크)을 docker build -t comfortablemove-backend:dev backend/로 빌드하여 314MB 이미지를 만들고, minikube image load comfortablemove-backend:dev로 클러스터에 직접 로드하였다. deployment.yaml의 imagePullPolicy를 IfNotPresent로 두어 외부 레지스트리 pull 시도가 발생하지 않도록 구성하였다.

2-5. 단계별 트러블슈팅
첫 배포에서 파드 3개가 모두 startup에서 종료되는 문제가 발생하였다. lifespan의 init_db()에서 PostgreSQL 연결을 시도하였으나 secret의 DATABASE_URL이 host.minikube.internal:5432를 가리키는 상태에서 socket.gaierror: Name or service not known으로 실패하였다. 원인을 단계별로 좁혀가면서 5단계의 트러블슈팅을 거쳤다.

첫째, host.minikube.internal이 minikube 노드의 /etc/hosts에는 등록되지만 Pod의 DNS 해석에는 노출되지 않는 점을 확인하였다. deployment.yaml에 hostAliases를 추가하여 192.168.65.254로 매핑하였으나 일부 클라이언트(asyncpg)에서 동일 에러가 지속되어, secret의 URL을 IP 직박 형태로 변경하였다.

둘째, Deployment의 selector immutability 제약을 확인하였다. kustomize의 deprecated commonLabels가 selector에도 적용되어 직접 deployment.yaml을 apply할 때 selector field is immutable 에러가 발생하였다. namespace 자체를 삭제 후 재배포하여 새 selector로 재생성하였고, kustomization.yaml의 commonLabels를 새 형식의 labels(includeSelectors:false)로 교체하였다.

셋째, CrashLoopBackOff backoff 누적 문제를 확인하였다. 의존성 미준비 상태로 떨어진 파드는 restart 카운트가 증가할수록 backoff 시간이 지수적으로 길어져 의존성을 복구해도 즉시 회복되지 않았다. kubectl rollout restart deploy/backend로 새 ReplicaSet을 생성하면서 backoff를 리셋하는 패턴을 학습하였다.

넷째, PostgreSQL 자격증명 불일치(role "user" does not exist) 에러를 분석하였다. host의 docker-compose가 띄운 postgres 컨테이너의 환경변수는 user/password로 설정되었지만 동일 에러가 반복되어 lsof -nP -iTCP:5432 -sTCP:LISTEN으로 호스트의 5432 listener를 점검한 결과, macOS 네이티브 PostgreSQL(parkseonggeun, PID 1155)이 5432를 점유하고 있음을 발견하였다. minikube 파드가 192.168.65.254:5432로 연결할 때 Docker Desktop의 vmnet을 거쳐 macOS 네이티브 postgres로 라우팅되어, docker-compose의 자격증명과 무관한 응답을 받고 있었다.

다섯째, docker network connect로 우회를 적용하였다. comfortablemove_db, comfortablemove_redis 컨테이너를 minikube docker network에 join 시켜 같은 docker bridge에서 통신하도록 하였고, 새 IP(192.168.49.3, 192.168.49.4)를 secret의 DATABASE_URL/REDIS_URL에 박았다. 이후 진단 파드(comfortablemove-backend:dev 이미지로 sleep 120)에서 asyncpg.connect를 직접 호출하여 OK: user 응답을 확인하였고, kubectl rollout restart로 백엔드 파드를 회복시켰다.

또한 호스트 docker-compose의 postgres volume이 이전 init 때의 자격증명을 보존하고 있어 .env의 user/password가 적용되지 않는 문제도 발생하여, docker compose down -v로 volume을 비우고 재기동하였다.

2-6. 10주차 검증 체크리스트 통과
모든 트러블슈팅 후 kubectl get pods -n comfortablemove에서 backend-f47bd7756-{8n4ql,bnqtg,k745v} 3개 파드 모두 1/1 Ready, 0 RESTARTS 상태를 확인하였다. kubectl get deploy backend -n comfortablemove로 READY 3/3, UP-TO-DATE 3, AVAILABLE 3을 확인하였고, kubectl get svc backend -n comfortablemove로 ClusterIP 10.97.122.67:80 매핑을 확인하였다.

kubectl port-forward -n comfortablemove svc/backend 18000:80으로 외부 접근 경로를 만든 후 GET /에서 {"message":"ComfortableMove Backend API","version":"1.0.0",...}, GET /api/v1/health에서 {"status":"healthy","services":{"database":"connected","redis":"connected","seoul_bus_api":"reachable"}} 응답을 확인하였다. 자동 재시작 검증으로 kubectl delete pod --grace-period=0 --force로 파드 1개를 강제 삭제한 직후 신규 파드(backend-f47bd7756-lpwf6)가 즉시 ContainerCreating으로 올라와 3/3 상태가 유지되는 것을 관찰하였다. ReplicaSet 컨트롤러가 desired state를 자동 복원하는 동작을 직접 확인하였다.

2-7. iOS-백엔드 통합 누락분 보강
9주차에 작성한 iOS-백엔드 통합 코드를 점검한 결과, 백엔드의 POST /api/v1/boarding/record가 정의되어 있음에도 iOS의 BLE 전송 결과(success/deviceNotFound/failure)를 백엔드에 기록하는 호출 코드가 없어 통계 API의 데이터 소스가 항상 비어 있는 상태임을 발견하였다.

ComfortableMove/Core/Manager/DeviceIdentityManager.swift를 신규 작성하여 UserDefaults 기반의 영구 device_id(UUID)를 관리하도록 하였다. ComfortableMove/Core/Manager/BoardingRecordService.swift를 신규 작성하여 BluetoothTransferResult를 백엔드의 notification_status Literal(success/device_not_found/failure)과 1:1 매핑하는 헬퍼와 fire-and-forget POST 호출을 구현하였다. HomeView.sendCourtesySeatNotification에서 BLE 콜백 직후 Task.detached로 백엔드 기록을 비동기 호출하도록 통합하여 UX를 차단하지 않도록 하였다.

백엔드 측에서는 backend/app/api/v1/boarding.py의 create_boarding_record 핸들러에 users_devices 자동 upsert 로직을 추가하였다. iOS가 처음 보내는 device_id가 users_devices에 없으면 ON DELETE SET NULL FK 제약으로 INSERT가 실패하던 문제를 해결하기 위해, device_id가 들어오면 SELECT 후 없으면 UserDevice를 즉시 생성하고 있으면 last_active_at을 갱신하도록 하였다. 회귀 테스트로 test_create_boarding_record_auto_registers_unknown_device(미등록 UUID로 POST → users_devices에 자동 생성 + boarding_records 정상 INSERT), test_create_boarding_record_maps_ios_status_values(iOS의 3개 status 값 모두 수락) 2개를 backend/tests/integration/test_api_boarding.py에 추가하였다.

검증 결과 iOS Xcode 빌드(iphonesimulator, arm64+x86_64) BUILD SUCCEEDED, 백엔드 통합 테스트 11/11 passed(기존 9 + 신규 2), 단위 테스트 39/40 passed(실패 1건은 Redis mock 사전 결함, 이번 변경 무관)을 확인하였다.

2-8. GitHub Actions 워크플로 정상화
push 후 main에 대한 GitHub Actions 실행을 점검하면서 CI/CD 양쪽이 누적 실패하고 있음을 발견하였다.

CD(.github/workflows/cd.yml)는 secrets.EC2_SSH_PRIVATE_KEY와 secrets.EC2_HOST가 GitHub repo에 등록되지 않아 ssh-keyscan -H ""에서 즉시 exit 1로 종료되고 있었다. 워크플로 첫 단계에 시크릿 가드 step을 추가하여, 두 시크릿 중 하나라도 비어있으면 ::warning::으로 알림 후 후속 step을 모두 if: steps.secrets.outputs.skip == 'false'로 건너뛰고 success로 종료하도록 변경하였다. 또한 paths 필터를 backend/**에서 backend/app/**, backend/Dockerfile, backend/requirements*.txt, backend/docker-compose.yml, backend/docker-compose.prod.yml, .github/workflows/cd.yml로 정밀화하여 README/매니페스트/테스트 단독 변경 시 EC2 배포가 트리거되지 않도록 하였다.

CI(.github/workflows/ci.yml)는 ENVIRONMENT=testing 환경변수가 설정된 상태에서 app.main import 시점의 Settings() 평가가 Literal validation으로 실패하고 있었다. backend/app/core/config.py의 environment Literal에 "testing"을 추가하여 4개 환경(development/staging/production/testing)을 모두 valid 값으로 허용하였고, backend/tests/conftest.py의 import 최상단에 os.environ.setdefault로 ENVIRONMENT/SEOUL_BUS_API_KEY/SECRET_KEY의 기본값을 보정하여 settings = get_settings()의 즉시 평가가 안전하도록 방어하였다.

이후 ModuleNotFoundError: No module named 'aiosqlite'가 새로 드러났다. tests/conftest.py가 sqlite+aiosqlite:///:memory: 드라이버를 사용하지만 backend/requirements.txt에 aiosqlite가 누락되어 있었다. requirements.txt의 Testing 섹션에 aiosqlite==0.19.0을 추가하여 해결하였다.

추가로 사전 결함이었던 backend/tests/unit/test_redis.py::test_clear_cache_pattern_success/no_keys 두 케이스가 production code(scan_iter async generator) 대신 keys() return으로 잘못 모킹되어 있는 문제를 발견하였다. async def fake_scan_iter(match, count): yield k 형태의 async generator로 mock_client.scan_iter를 교체하고, mock_client.delete.call_count == 2와 assert_any_call("bus:01234")/("bus:56789")로 단건 delete 2회 호출을 검증하도록 수정하였다.

2-9. 워크플로 검증
모든 수정 후 main에 push하여 CI/CD 양쪽이 success로 통과하는 것을 gh run watch로 확인하였다. CI - Test & Lint 1m14s success(test 76개 + integration 11개, docker-build-check 통과), CD - Deploy to EC2 6s success(시크릿 미등록 → skip 워닝 후 정상 종료) 결과를 얻었다.


3. 프로젝트 주차 진행 결과
Kubernetes 측면에서는 minikube v1.37.0(driver=docker, kubernetes-version=v1.34.0)으로 로컬 클러스터를 기동하고, infra/k8s/ 디렉토리에 namespace.yaml, configmap.yaml, secret.example.yaml, deployment.yaml, service.yaml, kustomization.yaml, README.md, .gitignore의 8개 파일을 작성하였다. backend/Dockerfile로 빌드한 314MB 이미지를 minikube image load로 로드한 후 kubectl apply -k infra/k8s/로 일괄 배포하였다. Deployment의 replicas=3, RollingUpdate(maxSurge=1, maxUnavailable=0), envFrom으로 ConfigMap+Secret 주입, liveness/readiness probe, resource requests/limits을 모두 적용하였다. Service는 ClusterIP로 80→8000 포트 매핑하고 kubectl port-forward로 외부 접근 경로를 검증하였다.

검증 결과 파드 3개 모두 1/1 Ready 0 RESTARTS, GET /api/v1/health에서 database/redis/seoul_bus_api 모두 connected/reachable 응답, kubectl delete pod --force로 파드 1개 강제 삭제 시 즉시 신규 파드 생성으로 3/3 유지를 확인하였다. ReplicaSet 컨트롤러의 self-healing 동작을 직접 관찰하였다.

iOS-백엔드 통합 측면에서는 ComfortableMove/Core/Manager/DeviceIdentityManager.swift, BoardingRecordService.swift 2개 파일을 신규 작성하여 익명 device_id 관리와 POST /api/v1/boarding/record 호출을 구현하였다. HomeView.swift에서 BLE 콜백 직후 fire-and-forget으로 백엔드 기록을 트리거하도록 통합하였다. 백엔드의 backend/app/api/v1/boarding.py에 users_devices 자동 upsert 로직을 추가하여 미등록 device_id의 FK 위반을 방지하였고, backend/tests/integration/test_api_boarding.py에 회귀 테스트 2개를 추가하였다. iOS Xcode 빌드 SUCCEEDED, 백엔드 통합 테스트 11/11 PASSED를 확인하였다.

GitHub Actions 워크플로 측면에서는 .github/workflows/cd.yml에 시크릿 가드 step과 paths 정밀화를 적용하였고, .github/workflows/ci.yml의 ENVIRONMENT=testing 환경에서도 통과하도록 backend/app/core/config.py의 Literal에 "testing"을 추가하고 backend/tests/conftest.py에 import-time 환경변수 보정을 넣었다. backend/requirements.txt에 누락된 aiosqlite를 추가하고 backend/tests/unit/test_redis.py의 scan_iter mock을 production과 일치시켰다. 최종 push로 CI/CD 양쪽 success 확인.

문서 측면에서는 infra/k8s/README.md에 사전 준비/배포 절차/검증 체크리스트/정리 명령을 정리하였고, infra/k8s/.gitignore로 실제 secret.yaml의 커밋을 차단하였다. 커밋 단위는 [Chore] K8s Secret 템플릿 및 실제 Secret 커밋 차단, [Feat] 백엔드 K8s 매니페스트 및 kustomize 진입점 추가, [Docs] infra/k8s 배포 및 검증 절차 문서 작성, [Fix] CI 환경(ENVIRONMENT=testing) 검증 통과 및 Redis 패턴 삭제 mock 정정, [Fix] CD 워크플로 시크릿 가드 및 트리거 경로 정밀화, [Fix] requirements.txt 에 aiosqlite 추가 — CI 테스트 의존성 누락 해결의 6개로 의미 단위 분리하였다. iOS 측은 [Feat] 백엔드 프록시 연동 및 배려석 알림 기록 전송으로 단일 커밋, dev 브랜치에 push하였다.

티스토리: https://foden2000.tistory.com/144
GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1


4. 기타(문제점, 해결방법, 자기평가 등)

4-1. 문제점 및 해결방법
호스트 5432 포트 충돌이 가장 큰 디버깅 과제였다. minikube 파드가 host.minikube.internal:5432로 도달은 가능하지만 PostgreSQL이 role "user" does not exist 에러를 응답하였다. lsof -nP -iTCP:5432 -sTCP:LISTEN으로 호스트의 listener를 점검하기 전까지는 docker-compose의 postgres 자격증명 문제로 오인하였다. 점검 결과 macOS 네이티브 PostgreSQL(PID 1155)이 5432를 점유 중이었고, Docker Desktop의 vmnet을 통한 라우팅이 docker-compose가 아닌 네이티브 인스턴스로 가고 있었다. docker network connect minikube comfortablemove_db/comfortablemove_redis로 같은 docker bridge에 join 시키고 새 IP(192.168.49.3/192.168.49.4)를 secret에 박는 우회로 해결하였다. 호스트 OS의 백그라운드 프로세스가 컨테이너 네트워크와 충돌할 수 있다는 점을 학습하였다.

host.minikube.internal의 Pod DNS 미해석 문제를 발견하였다. minikube 노드의 /etc/hosts에는 host.minikube.internal → 192.168.65.254가 등록되지만 Pod의 CoreDNS 해석에는 노출되지 않아 asyncpg가 socket.gaierror: Name or service not known을 반환하였다. deployment.yaml에 hostAliases로 직접 매핑을 추가하였고, asyncpg의 일부 경로에서 /etc/hosts가 무시되는 케이스를 만나 결국 IP 직박으로 전환하였다. K8s에서 클러스터 외부 호스트네임을 다룰 때는 ExternalName Service나 hostAliases, IP 직박 중 워크로드 특성에 맞춰 선택해야 한다는 점을 학습하였다.

CrashLoopBackOff backoff가 누적되는 문제로 디버깅 사이클이 길어졌다. 의존성을 복구해도 backoff 시간이 지수적으로 늘어나 즉시 회복되지 않았고, kubectl rollout restart로 새 ReplicaSet을 만들면서 backoff를 리셋하는 패턴을 익혔다. 또한 progress deadline이 기본 600초여서 deadline 초과로 워치가 종료되어도 파드는 여전히 백오프 중인 상태였다. 단순히 시간을 기다리기보다 명시적인 restart로 backoff를 끊는 것이 빠르다는 점을 체감하였다.

PostgreSQL volume의 자격증명 잔재 문제도 만났다. docker-compose.yml의 POSTGRES_USER/POSTGRES_PASSWORD가 .env에서 로드됨에도 불구하고 컨테이너가 user "user" does not exist를 반환하였다. postgres 이미지는 데이터 디렉토리가 비어있을 때만 init 스크립트를 실행하므로, 기존 volume이 다른 자격증명으로 init된 상태가 보존되고 있었다. docker compose down -v로 volume을 제거한 후 재기동하여 새 자격증명으로 init되도록 하였다.

GitHub Actions 워크플로 누적 실패가 매 push마다 알림으로 쌓이고 있었다. CD는 EC2_SSH_PRIVATE_KEY/EC2_HOST 시크릿 미등록으로, CI는 ENVIRONMENT=testing이 Literal["development","staging","production"]에 매칭되지 않아 import time에 ValidationError로 죽고 있었다. CD에는 시크릿 가드 step을 추가하여 미등록 시 워닝 후 success 종료하도록 하였고, CI는 Literal에 "testing"을 추가하고 conftest.py의 import-time 환경변수 보정을 넣어 해결하였다. 그 다음 단계에서 aiosqlite 의존성 누락이 드러나 requirements.txt에 추가하였고, 마지막으로 사전 결함이었던 Redis scan_iter mock 회귀를 production과 일치하도록 수정하였다. 워크플로 실패는 한 번에 한 가지 원인만 노출되므로, 한 단계씩 수정하고 push하면서 다음 실패 원인이 드러나기를 기다리는 패턴이 효율적이라는 점을 익혔다.

iOS-백엔드 통합 측면에서는 BoardingRecordService 호출이 누락된 상태였다는 사실을 9주차 보고서 작성 시점에 인지하지 못한 것이 아쉬웠다. 백엔드 통계 API의 데이터 소스가 비어 있다는 사실을 10주차에야 발견하면서, 통합 코드는 양쪽 호출 경로를 모두 그려야 정합성이 보장된다는 점을 재학습하였다.

4-2. 자기평가
가장 큰 성과는 Kubernetes 매니페스트를 손으로 작성하여 백엔드 API를 로컬 클러스터에 배포한 점이다. Pod, ReplicaSet, Deployment, Service, ConfigMap, Secret의 책임 분담을 매니페스트 작성 단계에서 직접 적용하였고, RollingUpdate strategy(maxSurge/maxUnavailable), liveness/readiness probe, resource requests/limits, envFrom 주입 등 실무에서 자주 쓰이는 옵션을 한 번에 다뤄볼 수 있었다. kubectl apply, get, describe, logs, exec, delete pod, rollout restart의 실제 사용 흐름을 트러블슈팅 과정에서 자연스럽게 익힌 점도 만족스러웠다.

self-healing을 직접 검증한 점이 학습 측면에서 의미 있었다. kubectl delete pod --grace-period=0 --force로 파드를 강제 삭제하자마자 ReplicaSet 컨트롤러가 새 파드를 즉시 생성하여 3/3 상태로 회복하는 동작을 관찰하면서, Kubernetes의 desired state 모델이 단순한 자동화 이상의 가치를 가진다는 점을 실감하였다.

호스트 5432 충돌 디버깅 과정도 학습 가치가 컸다. 환경변수, 시크릿, hostAliases, docker network까지 차례로 점검하면서 어디까지가 K8s 이슈이고 어디부터가 호스트 OS 이슈인지 경계를 좁혀가는 경험을 하였다. lsof로 호스트 listener를 확인한 시점에 비로소 macOS 네이티브 postgres가 원인임이 드러났는데, 컨테이너 환경에서도 호스트 OS의 background 프로세스가 영향을 줄 수 있다는 점은 한 번 겪지 않으면 알기 어려운 부분이었다.

GitHub Actions 워크플로를 정상화하면서 CI/CD를 단순한 자동화 도구가 아닌 코드와 동등한 수정 대상으로 다루는 감각을 익혔다. 시크릿 가드, paths 정밀화, Literal 확장, conftest import-time 보정, requirements 정리, mock 정정의 6가지 수정이 모두 워크플로 통과를 위해 필요했고, 한 번에 한 가지 실패만 드러나는 워크플로 디버깅 패턴을 체감하였다.

iOS-백엔드 통합 누락분을 보강하면서 클라이언트-서버 양쪽 호출 경로를 모두 검증하는 것의 중요성을 다시 확인하였다. 백엔드에 엔드포인트가 정의되어 있어도 클라이언트가 호출하지 않으면 그 데이터를 사용하는 후속 API(통계)는 비어 있게 되므로, 통합 작업은 양방향으로 그려야 한다는 점을 학습하였다.

아쉬운 점은 이번 주차에 PostgreSQL/Redis를 K8s 안에 배포하지 못한 점이다. 호스트 docker-compose에 의존하는 구성은 학습용으로는 충분하지만, StatefulSet과 PV/PVC, Helm chart 같은 영속성 패턴을 다음 주차로 미루었다. 또한 매니페스트 일부에 컨테이너 IP 직박이 들어가 재시작 시 IP가 변하면 secret을 갱신해야 하는 운영 부담이 있어, 다음 주차에서 ExternalName Service나 K8s 내부 StatefulSet으로 정리할 계획이다. CD 측면에서는 EC2 시크릿이 등록되지 않아 실제 배포는 수행되지 않은 상태이며, 다음 주차에서 EC2 인스턴스 또는 K8s 클라우드 환경에 실제 배포 사이클을 검증할 예정이다. Ingress(NGINX/Traefik), HPA(HorizontalPodAutoscaler), ServiceMonitor 등 관측/스케일링 패턴은 K8s 학습 후속 주차의 주제로 두었다.
