※ 임시 메모 — 11주차 정식 보고서 작성 전 작업 기록 (정리 후 추후 보강 예정)


1. 프로젝트 주차 목표
10주차에 구축한 K8s 학습 환경(minikube + 백엔드 Deployment 3 replicas)에서 iOS 시뮬레이터가 아닌 iPhone 실기기까지 통신 라인을 확장하여 iOS ↔ 백엔드 ↔ ESP32 BLE 하드웨어의 풀스택 통신을 직접 검증하는 것을 1차 목표로 한다. 동시에 10주차 작업 후 드러난 문제(K8s readinessProbe 가 health endpoint 의 외부 API 호출까지 트리거하여 서울 TOPIS 일일 한도(100 회) 가 5 분 만에 소진되는 누수, 백엔드 init_db 가 모델 모듈을 import 하지 않아 boarding_records/users_devices 테이블이 자동 생성되지 않는 누락)을 정리하여 백엔드의 데이터 수집 파이프라인을 정상화한다. 부수적으로 minikube 재구축 절차, Docker Desktop daemon 강제 재시작, 호스트 docker-compose deps 와 minikube docker network 의 IP 직박 매핑 등 운영 절차를 재현 가능한 형태로 기록한다.


2. 프로젝트 주차 진행 내용

2-1. 10주차 환경 재기동 및 Docker daemon 복구
세션 시작 시점에 Docker daemon 이 응답 불가 상태였다. docker info / docker ps 모두 timeout 으로 응답이 없었고 minikube start 가 PROVIDER_DOCKER_NOT_RUNNING 으로 실패하였다. osascript quit + pkill 로 Docker Desktop 을 강제 종료한 후 open -a Docker 로 재시작하였고, until 폴링으로 daemon ServerVersion 응답 여부를 감지하는 방식으로 ready 시점을 정확히 파악하였다.

2-2. minikube 재구축
기존 minikube 컨테이너는 host: Running 이지만 kubelet 이 "activating (auto-restart, Result: exit-code)" 상태로 494 회째 재시작 루프에 빠져 있었다. journalctl -u kubelet 으로 "failed to run Kubelet: unable to load bootstrap kubeconfig: /etc/kubernetes/bootstrap-kubelet.conf: no such file" 를 확인하였고, minikube delete 후 재생성하는 방식으로 깨끗하게 회복하였다. 컨테이너 안의 K8s 부트스트랩 파일이 손상된 케이스로, 재시작/start 만으로는 복구가 안 되고 컨테이너 자체를 재생성해야 한다는 점을 학습하였다.

2-3. iOS 실기기 통신 라인 구축
실기기는 시뮬레이터와 달리 localhost 를 못 쓰므로 Mac LAN IP(172.30.1.79) 로 백엔드를 노출해야 하였다. kubectl port-forward 의 default 가 127.0.0.1 only 이므로 --address 0.0.0.0 옵션으로 모든 인터페이스에 listen 시켰다. iOS Config.xcconfig 의 BACKEND_BASE_URL 을 LAN IP 로 변경하였다.

첫 호출 시 NSURLErrorDomain Code=-1009 "Local network prohibited" 에러가 발생하였다. iOS 14+ 의 로컬 네트워크 권한이 별도이고 NSAllowsArbitraryLoads(이미 적용됨) 로는 부족하다는 점을 확인하였다. Info.plist 에 NSLocalNetworkUsageDescription 과 NSBonjourServices(_http._tcp) 를 추가하였고, 첫 호출 시 권한 다이얼로그 → 허용 후 통신이 정상화되었다.

2-4. 백엔드 init_db 모델 등록 누락 fix
iOS BLE 결과를 백엔드에 POST 했을 때 "relation 'users_devices' does not exist" 에러가 발생하였다. backend/app/db/session.py 의 init_db 가 Base.metadata.create_all 을 호출하지만 모델 모듈(app.models.user_device, boarding_record) 을 import 하지 않아 metadata 에 테이블이 등록되지 않은 상태였다. 또한 if settings.debug 가드로 인해 ConfigMap 의 DEBUG="false" 환경에서는 create_all 자체가 호출되지 않고 있었다.

session.py 의 init_db 안에 from app.models import user_device, boarding_record (side-effect import) 를 추가하고, 가드를 settings.environment in ("development", "testing") 로 변경하였다. 학습 환경 일관성을 위해 ConfigMap 의 ENVIRONMENT 도 "production" → "development" 로 변경하였다.

2-5. readinessProbe 외부 API 트래픽 누수 차단
실기기 테스트 중 도착정보 API 가 "Key 인증실패: LIMITED NUMBER OF SERVICE REQUESTS EXCEEDS, 인증모듈 에러코드(22)" 로 거부되었다. 일일 100 회 한도가 짧은 시간 안에 소진된 원인을 추적한 결과, K8s readinessProbe 가 /api/v1/health 를 10 초 주기로 호출하고 health endpoint 가 seoul_bus_service.check_api_health() 로 /stationinfo/getStationByUid 를 직접 호출하는 구조였다. 파드 3 개 × 6 회/분 = 18 회/분 → 일일 한도가 약 5~6 분 만에 도달하는 계산이다.

해결로 backend/app/api/v1/health.py 에 /api/v1/health/ready 엔드포인트를 신설하여 DB·Redis 만 확인하고 외부 API 호출은 하지 않도록 분리하였다. infra/k8s/deployment.yaml 의 readinessProbe.httpGet.path 를 /api/v1/health/ready 로 교체하였다. /api/v1/health 는 수동/모니터링용으로 외부 API 까지 검증하는 기존 동작을 유지하였다.

2-6. minikube image 캐시 우회
백엔드 코드 수정 후 호스트 docker build → minikube image load 만으로는 minikube 안의 캐시된 이미지가 갱신되지 않아 옛 코드가 그대로 실행되는 문제를 만났다. minikube image rm 도 컨테이너가 이미지를 사용 중이라 must force 거부되었다. eval $(minikube docker-env) 로 minikube 내부 docker 컨텍스트로 전환한 뒤 그 안에서 직접 docker build 하여 layered diff 로 새 이미지가 즉시 반영되도록 하였다. 이후 kubectl rollout restart 로 새 이미지가 파드에 적용되었음을 확인하였다.

2-7. BLE 매칭 hack (DEV 임시)
ESP32 펌웨어가 BF_DREAM_143 으로 advertising 중이지만 사용자 위치(한산중학교 근처) 에 143 노선이 도착정보로 노출되지 않아 화면에 강동01 만 떠 있는 상황이었다. ESP32 펌웨어 변경 없이 BLE 흐름을 검증하기 위해 두 가지 임시 hack 을 iOS 에 적용하였다.

ComfortableMove/Core/Presentation/Home/HomeView.swift 의 refreshBusArrivals 에서 fetched 도착정보 앞에 mock 143 BusArrivalItem 을 항상 prepend 하도록 변경하였다(외부 API 응답 유무와 무관하게 사용자가 143 을 선택할 수 있도록). 또한 sendCourtesySeatNotification 에서 BLE 스캔/송신 시 화면 선택값과 무관하게 bleBusNumber = "143" 으로 강제하였다. 백엔드 boarding 기록은 화면 선택값(busName) 그대로 전송하여 통계 정확성은 보존하였다.

2-8. 풀스택 통신 검증
실기기에서 알림 버튼을 두 번(소리 ON/OFF 각 1 회) 누른 후 다음을 확인하였다. K8s 백엔드 파드 로그에 "POST /api/v1/boarding/record HTTP/1.1 201" 두 번 기록되었고, boarding_records 테이블에 동일한 device_id(d5030bf9-…) 의 두 행(route_name=143, bus_device_id=BF_DREAM_143, station_name=한산중학교, ars_id=25564, sound_enabled=t/f, notification_status=success) 이 존재하였다. users_devices 테이블에는 해당 device_id 가 자동 등록되었고 last_active_at 이 두 번째 호출 시점으로 갱신되었다(upsert 로직 정상 동작).


3. 프로젝트 주차 진행 결과
실기기 풀스택 통신: iPhone 실기기에서 GET /api/v1/bus/stations(라이브 응답 26 개 정류소 200 OK), BLE 알림 송신(BF_DREAM_143 매칭 → "✅ 데이터 전송 성공"), POST /api/v1/boarding/record(HTTP 201, DB 저장 확인)의 전체 흐름이 한 번의 사용자 동작으로 모두 통과하였다. iOS Info.plist 에 NSLocalNetworkUsageDescription 추가, kubectl port-forward --address 0.0.0.0 매핑, BACKEND_BASE_URL=http://172.30.1.79:8000 설정으로 LAN 노출 라인이 안정적으로 동작한다.

백엔드 데이터 파이프라인 정상화: init_db 의 모델 import 누락과 environment 가드를 fix 하여 boarding_records / users_devices 테이블이 컨테이너 첫 기동 시 자동 생성되도록 하였다. 미등록 device_id 자동 upsert(이전 주차에 추가) 와 결합되어 익명 사용자의 첫 호출도 FK 위반 없이 처리된다. 도착 후 통계 API 의 데이터 소스가 비어 있던 문제(9~10주차 미발견) 도 해소되었다.

readinessProbe 트래픽 누수 차단: /api/v1/health 와 /api/v1/health/ready 를 책임 분리하여 K8s probe 에서는 외부 API 를 호출하지 않도록 하였다. 파드 3 개 기준 분당 18 회 누수가 0 회로 줄어 서울 TOPIS 일일 한도 100 회는 사용자/모니터링 호출에만 소비된다.

운영 절차 재현 가능성 향상: Docker daemon 응답 불가 시 강제 재시작(osascript + pkill + open -a Docker), minikube 컨테이너 안의 kubeadm 부트스트랩 손상 시 minikube delete 재생성, minikube image 캐시 우회(eval $(minikube docker-env)), 호스트 deps 와 minikube 컨테이너의 docker network connect 매핑(IP 직박) 등 12 주차 이후에도 반복적으로 마주칠 운영 시나리오를 단계별로 기록하였다.

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1
iOS: https://github.com/BFDream-AutoEver/BFDream-iOS


4. 기타(문제점, 해결방법, 자기평가 등)

4-1. 문제점 및 해결방법
서울 TOPIS API 일일 100 회 한도가 readinessProbe 에 의해 5~6 분 만에 소진되는 누수를 발견하였다. K8s health endpoint 가 외부 의존성을 한 곳에 모두 검증하는 단일 패턴(흔한 설계) 이었지만, probe 가 그 endpoint 를 분당 다회 호출하는 구조와 결합되면 외부 API 한도가 무의식적으로 빠르게 소진된다. /health/ready(probe 전용) 와 /health(수동/모니터링) 를 분리하는 패턴으로 해결하였다.

iOS 14+ 로컬 네트워크 권한 누락으로 -1009 에러가 발생하였다. NSAllowsArbitraryLoads 만으로는 LAN 통신이 허용되지 않으며 NSLocalNetworkUsageDescription 별도 추가가 필요하다는 점을 학습하였다. NSBonjourServices 도 함께 등록하여 권한 트리거를 안정화하였다.

minikube image 캐시 문제로 호스트에서 빌드한 새 이미지가 minikube 안에 반영되지 않았다. 같은 태그(:dev) + IfNotPresent 조합에서 발생하는 흔한 함정이며, eval $(minikube docker-env) 로 minikube 내부 docker 컨텍스트에서 직접 빌드하는 방식으로 우회하였다.

호스트 docker-compose 와 minikube 컨테이너의 docker network 분리 문제는 10주차 발견사항이지만 11주차에 재현/재해결하였다. comfortablemove_db / comfortablemove_redis 를 docker network connect minikube 로 같은 docker bridge 에 join 시키고 새 IP(192.168.49.3 / 192.168.49.4) 를 secret 에 박아 통신을 회복하였다.

postgres volume 의 자격증명 잔재가 .env 의 신규 값을 덮어쓰지 않는 문제를 다시 만났다. postgres 이미지가 데이터 디렉토리 비어있을 때만 init 스크립트를 실행하는 동작 때문이며, docker compose down -v 로 volume 비우고 재기동하여 해결하였다(데이터 삭제는 사용자 명시 승인 후 진행).

ESP32 펌웨어와 iOS 화면 노출 버스 번호의 불일치 문제는 펌웨어 변경 없이 iOS 측 임시 hack 으로 우회하였다. 정식 환경에서는 펌웨어 advertising name 을 실제 노선 번호와 동기화하는 운영 정책이 필요하다.

4-2. 자기평가
가장 큰 성과는 iPhone 실기기에서 iOS ↔ 백엔드 ↔ ESP32 의 풀스택 통신을 한 번의 사용자 동작으로 검증한 점이다. 9~10주차에 각 레이어를 따로 검증했지만 실기기 환경에서 동시에 동작시킨 적은 없었고, 이번 주차에 LAN 노출/로컬 네트워크 권한/BLE 매칭/DB 저장의 4가지를 한꺼번에 통과시키면서 풀스택 시스템이 끊기는 지점이 어디인지 직접 체감할 수 있었다.

readinessProbe 의 트래픽 누수를 발견한 과정도 학습 가치가 컸다. "왜 일일 100 회가 5 분 만에 소진되었는가" 라는 질문에서 시작해 K8s probe periodSeconds × replicas × health endpoint 의 외부 API 호출 → 분당 18회의 산수에 도달하기까지, 단일 책임 원칙이 인프라 레이어에서도 동일하게 적용된다는 점을 체화하였다. health endpoint 분리 패턴(/health vs /health/ready) 은 production 시스템에서도 그대로 유효한 패턴이라 학습 가치가 높다.

운영 절차 측면에서 Docker daemon 강제 재시작, minikube 부트스트랩 복구, 이미지 캐시 우회, docker network bridge 매핑 등 "교과서에는 잘 안 나오지만 실제로 자주 마주치는" 케이스를 한 세션 안에서 모두 만나면서 디버깅 절차의 일관성을 다듬을 수 있었다. lsof 로 호스트 listener 점검, journalctl 로 컨테이너 안 systemd 서비스 추적, minikube ssh 로 노드 내부 진단 등 도구를 상황별로 골라 쓰는 감각도 늘었다.

iOS 임시 hack 두 군데(mock 143 도착정보 + BLE 송신 번호 고정) 는 실기기 검증을 빠르게 풀기 위한 trade-off 였지만, 정식 빌드 전에 반드시 되돌려야 한다. ESP32 펌웨어의 advertising name 정책 또는 백엔드의 mock 모드 토글 등 더 근본적인 해법은 다음 주차로 이연하였다.

아쉬운 점은 서울 TOPIS API 의 일일 한도가 이미 소진되어 도착정보 라이브 검증을 끝까지 하지 못한 점이다. /health/ready 분리 후 누수는 차단되었지만, 한도 reset 후 정상 노선(143 이 다니는 정류장 근처) 에서의 라이브 검증과 BLE hack 제거는 다음 주차에 진행할 계획이다. 또한 통계 API(/api/v1/statistics/user/{device_id}, /api/v1/statistics/global) 는 이제 데이터 소스가 채워져 동작 가능 상태이지만 iOS 측 화면이 없어 실제 호출 검증은 보류하였다.
