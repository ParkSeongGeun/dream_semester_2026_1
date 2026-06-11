# 15주차 활동 보고서

## 1. 프로젝트 주차 목표

15주차는 두 축으로 진행하였다. 첫째, **ArgoCD를 도입하여 GitOps 기반 CD(Continuous Deployment)** 를 구현한다. Git 저장소의 매니페스트가 단일 진실 공급원(Single Source of Truth)이 되어, 매니페스트 변경 시 ArgoCD가 자동으로 클러스터에 배포하고 롤백할 수 있는 구조를 완성한다. 둘째, **Ansible로 서버 프로비저닝을 자동화**한다. Inventory·Playbook·Role·Module·Variable 개념을 실제 Playbook에 적용하여 새 서버를 10분 이내에 초기 설정한다. 아울러 14주차에 미완료였던 **ECR 이미지 적재 검증**을 완결한다.

설정 작성에 그치지 않고, EKS 클러스터를 실제 생성하여 ArgoCD가 Git 변경을 자동 배포·롤백하는 것, Ansible Playbook이 실제 서버를 프로비저닝하는 것까지 직접 검증하는 것을 핵심 목표로 한다.


## 2. 프로젝트 주차 진행 내용

### 2-1. (14주차 완결) ECR 이미지 적재 검증

14주차 CI 파이프라인의 build-and-push job은 ECR 자격증명 미등록으로 graceful skip 상태였다. 이를 완결하기 위해 Terraform으로 ECR 리포지토리(`comfortablemove-backend`, lifecycle 최근 10개 유지)를 생성하고, GitHub Secrets(AWS 키, `ECR_REGISTRY`)를 등록하였다. 이후 backend 변경을 main에 push하자 CI가 실제로 이미지를 빌드하여 ECR에 푸시하였고, `aws ecr describe-images`로 **커밋 SHA 태그와 latest 태그가 적재**된 것을 직접 확인하였다.

### 2-2. EKS 클러스터 생성 (Terraform)

14주차 Terraform 환경(AWS)에 `eks` 모듈 호출을 추가하여 EKS 클러스터를 생성하였다. NAT Gateway 미사용 환경이므로 노드를 public 서브넷에 배치하여 IGW 경유로 ECR pull·control plane join이 가능하게 하였다(비용 절감). Kubernetes 버전은 지원 종료된 1.29 대신 1.33을 사용하였다. 노드 그룹(t3.medium x2)이 정상적으로 `Ready` 상태가 되어 클러스터가 가동되었다.

### 2-3. ArgoCD 설치 및 Application 등록

ArgoCD를 Helm으로 `argocd` 네임스페이스에 설치하였다. GitOps 배포 대상으로 `infra/k8s/eks-app`(postgres + redis + backend ECR 이미지)을 구성하고, ArgoCD Application을 다음 정책으로 등록하였다.

| 설정 | 값 | 의미 |
|------|-----|------|
| source | `infra/k8s/eks-app` @ main | Git 매니페스트 경로 |
| syncPolicy.automated | prune + selfHeal | Git 변경 자동 반영, drift 자동 복구 |
| syncOptions | CreateNamespace=true | 네임스페이스 자동 생성 |
| revisionHistoryLimit | 10 | 롤백용 히스토리 보존 |

> 보안상 민감 정보(DB 접속·SECRET_KEY·서울버스 키)는 Git에 두지 않고 `backend-secret`을 kubectl로 별도 생성하였다.

등록 직후 ArgoCD가 자동 동기화하여 **Synced · Healthy**(pod 4/4 Running) 상태가 되었다.

### 2-4. GitOps 자동 배포 및 롤백 검증

| 시나리오 | 동작 | 결과 |
|----------|------|------|
| 자동 배포 | `app.yaml`의 backend replicas 2→3 변경 후 push | 약 20초 내 클러스터에 자동 반영 (3/3) |
| 롤백 | Git revert로 3→2 되돌림 후 push | 약 20초 내 자동 복구 (2/2) |
| 히스토리 | ArgoCD revision history | 3개 리비전 기록(초기·3 replicas·2 replicas) — UI/CLI 롤백 가능 |

Git이 단일 진실 공급원으로 동작하여, 매니페스트 변경이 곧 배포이고 Git revert가 곧 롤백임을 실증하였다.

### 2-5. Ansible 서버 프로비저닝 자동화

새 서버를 Docker 구동 가능 상태로 초기 설정하는 Playbook을 role 기반으로 작성하였다.

| Ansible 개념 | 적용 |
|--------------|------|
| Inventory | `inventory.ini` — 대상 EC2 그룹·접속 정보 |
| Playbook | `playbook.yml` — common → docker role 순차 적용 |
| Role | `common`(시스템 업데이트·유틸리티), `docker`(Engine·compose) |
| Module | `dnf`, `systemd`, `user`, `get_url`, `command` |
| Variable | `vars/main.yml` — 패키지 목록, compose 버전 |

실제 EC2에 적용한 결과 **총 71초**(목표 10분 대비 대폭 단축)에 `ok=13 changed=3 failed=0`으로 완료되었으며, 재실행 시 멱등하게 통과함을 확인하였다.


## 3. 프로젝트 주차 진행 결과

| 항목 | 검증 결과 |
|------|-----------|
| ECR 적재 (14주차 완결) | CI → ECR push, SHA + latest 태그 적재 확인 |
| EKS 클러스터 | k8s 1.33, 노드 2개 Ready |
| ArgoCD 설치 | Helm 설치, Application Synced + Healthy (4/4 pod) |
| GitOps 자동 배포 | 매니페스트 변경(2→3) → 20초 내 자동 반영 |
| GitOps 롤백 | Git revert(3→2) → 20초 내 자동 복구, 히스토리 3리비전 |
| Ansible 프로비저닝 | EC2 초기 설정 71초, 멱등성 확인 |

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1


## 4. 기타 (문제점, 해결방법, 자기평가)

### 4-1. 문제점 및 해결방법

| 증상 | 원인 | 해결 |
|------|------|------|
| EKS 생성 실패 (unsupported version 1.29) | k8s 1.29 EKS 지원 종료 | 지원 버전 조회 후 1.33으로 변경 |
| 노드가 인터넷 접근 불가 우려 | 노드 private 배치 + NAT Gateway 없음 | 노드를 public 서브넷에 배치(IGW 경유) |
| Ansible 실행 실패 (yaml callback) | community.general.yaml callback 제거됨 | `result_format = yaml`로 교체 |
| Ansible 패키지 충돌 | Amazon Linux 2023은 curl-minimal 기본 | common_packages에서 curl 제외 |
| backend pod RESTARTS | postgres 준비 전 alembic 시도 | readinessProbe·재시작으로 자동 정상화 |

### 4-2. 자기평가

ArgoCD를 통해 GitOps의 핵심 원리를 실제로 체감하였다. 기존 CD(14주차 EC2 SSH 배포)는 "푸시(push) 기반"으로 외부에서 클러스터에 명령을 내리는 방식이었다면, ArgoCD는 "풀(pull) 기반"으로 클러스터 내 컨트롤러가 Git을 지속 관찰하여 스스로 동기화한다. 매니페스트 변경이 곧 배포, Git revert가 곧 롤백이 되는 선언적 운영을 직접 검증하면서, 클러스터 상태가 Git에 항상 수렴(self-heal)하는 GitOps의 강점을 이해하였다.

Ansible에서는 명령형 셸 스크립트(14주차 user-data)와 달리, 멱등성을 갖춘 선언적 프로비저닝의 장점을 확인하였다. 동일 Playbook을 이미 설정된 서버에 재실행해도 변경이 없으면 안전하게 통과하므로, 서버 수가 늘어도 동일 환경을 일관되게 재현할 수 있다.

또한 14주차 미완료였던 ECR 적재를 완결하여, CI가 빌드한 이미지가 레지스트리에 보관되고 이를 EKS가 pull하여 ArgoCD로 배포하는 **CI → 레지스트리 → CD 전체 파이프라인**을 하나로 연결하였다.

아쉬운 점은 EKS·ArgoCD가 시간당 과금되므로 상시 운영보다는 실습 후 `terraform destroy`로 환경을 정리해야 한다는 점이다. 또한 GitHub Webhook을 ArgoCD에 연동하면 폴링 없이 즉시 동기화가 가능하나, 이번에는 hard refresh로 동기화를 트리거하여 검증하였다.
