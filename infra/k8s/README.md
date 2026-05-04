# infra/k8s — ComfortableMove 백엔드 Kubernetes 매니페스트

10주차 학습 산출물. **로컬 minikube** 클러스터에 백엔드 API 만 배포 (DB/Redis 는 외부 — `host.minikube.internal` 또는 클라우드 RDS/ElastiCache 가리킴).

## 구성

| 파일 | 종류 | 역할 |
|---|---|---|
| `namespace.yaml` | Namespace | `comfortablemove` 네임스페이스 |
| `configmap.yaml` | ConfigMap | 비민감 환경변수 (port, log level, TTL 등) |
| `secret.example.yaml` | Secret 템플릿 | DB URL / Redis URL / API Key / SECRET_KEY (실제 값으로 채워 `secret.yaml` 로 복사) |
| `deployment.yaml` | Deployment | `replicas: 3`, RollingUpdate, liveness/readiness probe |
| `service.yaml` | Service | ClusterIP, port 80 → targetPort 8000 |
| `kustomization.yaml` | Kustomization | 한 번에 apply |

## 사전 준비

```bash
# 도구
kubectl version --client          # v1.31+ 권장
minikube version                  # v1.30+ 권장
docker version                    # daemon 실행 중

# 클러스터 시작
minikube start --driver=docker --kubernetes-version=v1.34.0
```

## 배포 절차

```bash
# 1) Secret 생성 (커밋 금지, .gitignore 됨)
cp infra/k8s/secret.example.yaml infra/k8s/secret.yaml
# secret.yaml 의 CHANGE_ME 값들을 실제 값으로 수정

# 2) 백엔드 이미지 빌드 (호스트 도커)
docker build -t comfortablemove-backend:dev backend/

# 3) 이미지 minikube 에 로드 (외부 레지스트리 없이)
minikube image load comfortablemove-backend:dev

# 4) 일괄 배포
kubectl apply -k infra/k8s/

# 5) 상태 확인
kubectl get pods -n comfortablemove -w
kubectl get svc -n comfortablemove
```

## 검증 — 10주차 목표 체크리스트

```bash
# 파드 3개 Running
kubectl get pods -n comfortablemove
# expected: backend-xxx-xxx 3개 모두 Running, 1/1 Ready

# 상세 정보
kubectl describe deployment backend -n comfortablemove

# 로그 (특정 파드)
kubectl logs -n comfortablemove deploy/backend --tail=50

# 컨테이너 접속
kubectl exec -it -n comfortablemove deploy/backend -- /bin/sh

# 자동 재시작 검증 — 파드 강제 삭제 후 새로 뜨는지 확인
kubectl delete pod -n comfortablemove -l app.kubernetes.io/name=backend --field-selector=status.phase=Running --grace-period=0 --force | head -1
kubectl get pods -n comfortablemove -w     # 새 파드가 ContainerCreating → Running 으로 올라옴

# 외부 접근 (포트포워드)
kubectl port-forward -n comfortablemove svc/backend 8000:80
# 다른 터미널에서:
curl http://localhost:8000/
curl http://localhost:8000/api/v1/health
```

## 정리

```bash
kubectl delete -k infra/k8s/        # 또는 namespace 만 지워도 됨
kubectl delete ns comfortablemove
minikube stop                       # 클러스터 일시 정지
# minikube delete                   # 완전 삭제 (캐시까지)
```

## 다음 단계 (이번 주차 범위 외)

- DB/Redis 도 K8s 안으로 이전 (StatefulSet + PV/PVC 또는 Helm chart)
- Ingress (NGINX 또는 Traefik) + cert-manager
- HPA(HorizontalPodAutoscaler)
- 별도 환경(dev/prod) overlay 추가 (kustomize overlay 패턴)
