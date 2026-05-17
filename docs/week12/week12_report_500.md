필수 목표
목표 (500자 이내)
prometheus-fastapi-instrumentator를 백엔드에 추가하고 Helm Chart로 패키징하는 것과 kube-prometheus-stack을 minikube에 설치하여 Prometheus, Grafana, AlertManager 기반 관측 가능성 파이프라인을 완성하는 두 축으로 구성되었다. ServiceMonitor로 백엔드 메트릭을 15초 간격으로 자동 수집하고 PrometheusRule로 5xx 에러율 5% 초과 및 p95 응답시간 1초 초과 시 경보를 정의하며 AlertManager가 이메일로 발송하는 완전한 모니터링 체계를 구현한다.


필수 진행내용
진행내용 (500자 이내)
prometheus-fastapi-instrumentator를 requirements.prod.txt에 추가하고 app/main.py에 Instrumentator().instrument(app).expose(app)를 추가하여 /metrics 엔드포인트를 노출하였다. minikube docker-env 환경에서 --no-cache로 재빌드 후 롤아웃하였다. charts/comfortablemove/ 아래 8개 템플릿을 작성하고 helm lint를 통과시켰다. kube-prometheus-stack을 monitoring 네임스페이스에 설치하고 null 리시버 추가와 Gmail 앱 비밀번호를 적용하여 AlertManager를 정상화하였다. infra/k8s/monitoring/ 아래 servicemonitor.yaml, prometheusrule.yaml, grafana-dashboard.yaml을 생성하여 적용하였다.


필수 진행결과
진행결과 (500자 이내)
백엔드 파드 3개가 job: backend, health: up 상태로 Prometheus에 등록되어 15초 간격으로 메트릭이 수집되고 있다. AlertManager는 2/2 Running 상태로 Gmail 앱 비밀번호 적용 후 정상화되었고 warning/critical 알림 발생 시 phd0328@gmail.com으로 발송된다. Grafana에는 grafana-sc-dashboard 사이드카가 comfortablemove.json을 자동 로드하여 요청 처리량, 5xx 에러율, p95 응답시간, CPU, 메모리 등 5개 패널이 30초 갱신으로 동작한다. Helm Chart는 helm lint 검증을 통과하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
requirements.prod.txt와 requirements.txt가 분리된 구조에서 신규 패키지를 requirements.txt에만 추가하여 운영 이미지에 ModuleNotFoundError가 발생하였다. 두 파일 모두 수정하고 --no-cache 재빌드로 해결하였다. AlertManager config 교체 시 null 리시버 정의를 누락하여 undefined receiver null 오류로 READY=0이 되었고 receivers에 null 항목을 추가하여 해결하였다. Gmail SMTP는 2022년 이후 일반 비밀번호 접근이 차단되어 앱 비밀번호를 발급하였다. 자기평가: FastAPI 앱에서 Grafana 시각화까지 관측 파이프라인 전체를 구현하며 Prometheus Operator의 동적 설정 반영 구조를 체감하였다.
