1. 프로젝트 주차 목표

12주차는 두 축으로 구성되었다. 첫 번째 축은 백엔드에 Prometheus 메트릭 수집 기능을 추가하고, 이를 Helm Chart로 패키징하여 재사용 가능한 배포 단위로 만드는 것이다. 두 번째 축은 kube-prometheus-stack(Prometheus + Grafana + AlertManager)을 minikube에 설치하고, ServiceMonitor로 백엔드 메트릭을 자동 수집하며, PrometheusRule로 임계치 초과 시 이메일 알림이 발송되는 관측 가능성(observability) 파이프라인을 완성하는 것이다.


2. 프로젝트 주차 진행 내용

2-1. Helm Chart 구조 설계 및 생성

charts/comfortablemove/ 디렉터리 아래 Chart.yaml, values.yaml, values-dev.yaml, values-prod.yaml 그리고 templates/ 하위에 deployment.yaml, service.yaml, configmap.yaml, servicemonitor.yaml, hpa.yaml, ingress.yaml, _helpers.tpl을 작성하였다.

values.yaml은 환경 공통 기본값(replicas=2, hpa.enabled=true, metrics.enabled=true, metrics.path=/metrics)을 담고, values-dev.yaml은 replicas=1과 dev.api.comfortablemove.com 호스트를, values-prod.yaml은 replicas=3과 더 큰 리소스 제한을 가진다. deployment.yaml에는 prometheus.io/scrape 어노테이션을 포함하여 Prometheus가 파드 직접 스크래핑도 지원하도록 하였다. helm lint로 문법 검증을 통과하였다.

2-2. 백엔드 /metrics 엔드포인트 추가

prometheus-fastapi-instrumentator==6.1.0을 requirements.txt와 requirements.prod.txt 양쪽에 추가하였다. app/main.py의 라우터 등록 후 Instrumentator().instrument(app).expose(app)을 한 줄 추가하여 /metrics 엔드포인트를 노출하였다. 이 엔드포인트는 HTTP 요청 수, 요청 처리 시간, 상태 코드별 카운터 등 표준 Prometheus 형식 메트릭을 제공한다.

2-3. Docker 이미지 재빌드 및 롤아웃

Dockerfile이 requirements.prod.txt를 사용하는 다단계 빌드 구조임을 확인하였다. requirements.prod.txt에 패키지를 추가한 후 eval $(minikube docker-env) && docker build --no-cache -t comfortablemove-backend:dev ./backend 로 minikube 내부 Docker 컨텍스트에서 캐시 없이 재빌드하였다. kubectl rollout restart deployment/backend -n comfortablemove로 롤아웃을 완료하였고, 파드 포트포워드로 curl localhost:18001/metrics 를 직접 호출하여 python_gc_objects_collected_total 등 Prometheus 메트릭이 정상 반환됨을 확인하였다.

2-4. kube-prometheus-stack 설치 및 AlertManager 설정

helm repo add prometheus-community 후 kube-prometheus-stack을 monitoring 네임스페이스에 설치하였다. 초기 AlertManager 기동 실패(READY 0/1)의 원인은 기본 라우트에서 참조하는 null 리시버가 커스텀 config에 정의되지 않은 것이었다. receivers 목록에 - name: "null" 항목을 추가하고 기본 route receiver를 "null"로 설정하여 해결하였다.

Gmail SMTP 설정은 구글이 2022년 이후 일반 비밀번호로의 SMTP 접근을 차단하였으므로 2단계 인증 후 앱 비밀번호(16자리)를 발급받아 smtp_auth_password에 적용하였다. alertmanager.config 전체를 /tmp/kube-prometheus-values.yaml 파일로 관리하여 helm upgrade -f 옵션으로 반영하였다. 업그레이드 후 alertmanager-kube-prometheus-stack-alertmanager-0이 2/2 Running 상태로 정상 기동되었다.

2-5. ServiceMonitor 및 PrometheusRule 적용

infra/k8s/monitoring/servicemonitor.yaml을 생성하여 app.kubernetes.io/name=backend 레이블로 백엔드 서비스를 선택하고 port: http, path: /metrics, interval: 15s로 스크래핑을 설정하였다. release: kube-prometheus-stack 레이블을 추가하여 Prometheus Operator가 이 ServiceMonitor를 인식하도록 하였다.

infra/k8s/monitoring/prometheusrule.yaml에는 두 가지 알림 규칙을 정의하였다. HighErrorRate는 5분간 HTTP 5xx 비율이 5%를 초과하면 2분 유지 후 critical로 발동되고, HighResponseLatency는 p95 응답시간이 1초를 초과하면 5분 유지 후 warning으로 발동된다. 두 CRD 모두 kubectl apply 후 존재를 확인하였다.

2-6. Prometheus 타깃 수집 확인

kubectl proxy를 통해 Prometheus API에 접근하여 /api/v1/targets를 조회하였다. serviceMonitor/comfortablemove/backend/0 잡이 목록에 나타났고, 백엔드 3개 파드 각각이 job: backend, health: up, lastError: "" 상태임을 확인하였다. 15초 간격으로 /metrics가 정상 스크래핑되고 있다.

2-7. Grafana 대시보드 구성

infra/k8s/monitoring/grafana-dashboard.yaml을 ConfigMap으로 작성하고 grafana_dashboard: "1" 레이블을 부여하였다. kube-prometheus-stack이 배포한 grafana-sc-dashboard 사이드카가 NAMESPACE=ALL 설정으로 전 네임스페이스의 ConfigMap을 감시하여 /tmp/dashboards/comfortablemove.json을 자동으로 로드하였다.

대시보드는 5개 패널로 구성하였다. (1) 요청 처리량(req/s), (2) 5xx 에러율(%), (3) p95 응답시간(초), (4) 백엔드 컨테이너 CPU 사용량(cores), (5) 메모리 사용량(MiB). 각 패널은 30초 자동 갱신으로 실시간 모니터링이 가능하다.


3. 프로젝트 주차 진행 결과

Helm Chart 완성: charts/comfortablemove/ 아래 8개 템플릿이 helm lint를 통과하였다. values-dev.yaml과 values-prod.yaml로 환경별 배포 분기가 가능하다.

/metrics 엔드포인트 확인: 재빌드된 이미지에서 curl로 Prometheus 형식 메트릭 반환을 직접 확인하였다.

Prometheus 스크래핑 정상 동작: 백엔드 파드 3개가 모두 health: up으로 15초마다 수집되고 있다.

AlertManager 이메일 설정 완료: Gmail 앱 비밀번호 적용 후 2/2 Running. warning/critical 알림 발생 시 phd0328@gmail.com으로 발송된다.

Grafana 대시보드 자동 로드: comfortablemove.json이 /tmp/dashboards/ 에 자동 배치되어 Grafana UI에서 5개 메트릭 패널을 즉시 확인할 수 있다.

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1
iOS: https://github.com/BFDream-AutoEver/BFDream-iOS


4. 기타(문제점, 해결방법, 자기평가 등)

4-1. 문제점 및 해결방법

requirements.prod.txt 분리로 인한 패키지 누락이 발생하였다. 프로젝트에 requirements.txt(개발)와 requirements.prod.txt(운영)가 분리되어 있었고 Dockerfile은 requirements.prod.txt만 사용한다. prometheus-fastapi-instrumentator를 requirements.txt에만 추가한 채 이미지를 빌드하였더니 운영 이미지에는 패키지가 없어 ModuleNotFoundError가 발생하였다. requirements.prod.txt에도 추가하고 --no-cache로 재빌드하여 해결하였다. 개발/운영 의존성 파일을 이중 관리할 때 새 패키지 추가 시 양쪽을 모두 수정해야 한다는 점을 학습하였다.

AlertManager null 리시버 미정의 오류가 발생하였다. kube-prometheus-stack 기본 AlertManager 설정은 Watchdog 등을 null 리시버로 라우팅하는데, 커스텀 config를 완전히 교체하면서 null 리시버 정의가 빠졌다. "undefined receiver null"로 AlertManager가 READY=0 상태가 되었고 receivers 목록에 - name: "null"을 추가하여 해결하였다. AlertManager config를 교체할 때 기존 라우팅 체계에서 참조하는 모든 리시버를 반드시 정의해야 한다는 점을 배웠다.

Gmail SMTP 앱 비밀번호 필수화를 인지하지 못하였다. 구글은 2022년부터 보안 수준이 낮은 앱의 SMTP 접근을 전면 차단하였으므로 일반 계정 비밀번호로는 연결이 불가하다. 2단계 인증 활성화 후 앱 비밀번호를 발급하여 smtp_auth_password에 적용하였다.

4-2. 자기평가

Prometheus 관측 파이프라인 전체를 직접 구현하였다. FastAPI 앱 → /metrics 노출 → ServiceMonitor로 Prometheus 스크래핑 → PrometheusRule로 알림 정의 → AlertManager로 이메일 발송, Grafana 대시보드 자동 로드까지 각 단계가 어떻게 연결되는지 체감하였다. 특히 Prometheus Operator가 ServiceMonitor CRD를 감시하여 스크래핑 설정을 동적으로 반영하는 구조는 기존 정적 설정 방식과의 차이를 명확하게 이해하는 계기가 되었다.

Helm Chart 구조 설계도 의미 있는 학습이었다. values.yaml, values-dev.yaml, values-prod.yaml의 계층적 오버라이드 방식으로 환경별 차이를 최소한의 파일로 관리하는 패턴을 체화하였다.

아쉬운 점은 Helm Chart를 직접 minikube에 helm install로 배포하는 단계까지 완료하지 못한 것이다. 현재는 kustomize 방식으로 배포된 기존 백엔드 위에 ServiceMonitor와 PrometheusRule을 별도로 적용하였다. 또한 실제 경보 발송은 임계치를 인위적으로 초과시키지 않아 이메일 수신까지는 검증하지 못하였다.
