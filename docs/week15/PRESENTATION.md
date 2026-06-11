# 15주차 발표 데모 가이드

## 1. 접속 정보

| 대상 | 주소 | 인증 |
|------|------|------|
| 기존 서비스 (EC2+RDS+ALB, 14주차) | https://comfortablemove.com/api/v1/health | - |
| EKS 앱 (ArgoCD 배포, 15주차) | http://a8c6856b0b94044859c2aac9e092f1ba-1616273185.ap-northeast-2.elb.amazonaws.com/api/v1/health | - |
| ArgoCD UI | https://localhost:8080 | admin / (open-ui.sh 실행 시 표시) |

> EKS LoadBalancer 주소가 바뀌면 확인:
> `kubectl get svc backend -n comfortablemove`

## 2. 발표 전 준비 (1분)

```bash
# ArgoCD UI 터널 띄우기 (이 창은 켜둔 채로)
cd infra/argocd && ./open-ui.sh
```

브라우저 탭 3개 준비:
1. https://comfortablemove.com/api/v1/health  (기존 클라우드 서비스)
2. EKS 앱 LoadBalancer 주소  (ArgoCD가 배포한 같은 앱)
3. https://localhost:8080  (ArgoCD UI)

## 3. 발표 흐름

### (1) 인프라 전체 그림
- 14주차: EC2 + docker-compose로 `comfortablemove.com` 운영
- 15주차: 같은 앱을 EKS + ArgoCD GitOps로 배포

### (2) ArgoCD UI 투어
- `comfortablemove` Application — **Synced / Healthy**
- 리소스 트리: Deployment(backend·postgres·redis) → ReplicaSet → Pod
- Sync Policy: Automated (prune + selfHeal)

### (3) GitOps 라이브 데모 (핵심)
```bash
# 1) 매니페스트 수정: replicas 2 → 3
vi infra/k8s/eks-app/app.yaml      # backend replicas: 3

# 2) Git push
git add infra/k8s/eks-app/app.yaml && git commit -m "demo: scale to 3" && git push

# 3) ArgoCD UI 에서 ~20초 내 Pod 3개로 자동 증가 관찰 (자동 배포)
#    (즉시 보려면 UI 의 REFRESH 버튼 또는 아래)
kubectl -n argocd annotate application comfortablemove argocd.argoproj.io/refresh=hard --overwrite
```

### (4) 롤백 데모
- ArgoCD UI → `History and Rollback` → 이전 리비전 선택
- 또는 GitOps 방식: `git revert` 후 push → 자동 복구

### (5) Ansible (서버 프로비저닝)
```bash
cd infra/ansible
ansible-playbook playbook.yml        # EC2 초기설정 71초, 멱등 재실행
```

## 4. 발표 후 정리 (과금 중단)

EKS는 시간당 ~$0.21 과금되므로 발표가 끝나면 정리한다.

```bash
cd infra/terraform
terraform destroy -target=module.eks    # EKS만 정리 (기존 서비스는 유지)
```
