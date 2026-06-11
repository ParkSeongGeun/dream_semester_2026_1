# 15주차 활동 보고서

## 1. 프로젝트 주차 목표

15주차는 두 축으로 진행하였다. 첫째, ArgoCD를 도입하여 GitOps 기반 CD(Continuous Deployment)를 구현한다. Git 저장소의 매니페스트가 단일 진실 공급원(Single Source of Truth)이 되어, 매니페스트 변경 시 ArgoCD가 자동으로 클러스터에 배포하고 롤백할 수 있는 구조를 완성한다. 둘째, Ansible로 서버 프로비저닝을 자동화한다. Inventory, Playbook, Role, Module, Variable 개념을 실제 Playbook에 적용하여 새 서버를 10분 이내에 초기 설정한다. 아울러 14주차에 미완료였던 ECR 이미지 적재 검증을 완결한다.

설정 작성에 그치지 않고, EKS 클러스터를 실제 생성하여 ArgoCD가 Git 변경을 자동 배포하고 롤백하는 것, Ansible Playbook이 실제 서버를 프로비저닝하는 것까지 직접 검증하는 것을 핵심 목표로 한다.


## 2. 프로젝트 주차 진행 내용

### 2-1. (14주차 완결) ECR 이미지 적재 검증

14주차 CI 파이프라인의 build-and-push job은 ECR 자격증명 미등록으로 graceful skip 상태였다. 이를 완결하기 위해 Terraform으로 ECR 리포지토리(comfortablemove-backend, lifecycle 최근 10개 유지)를 생성하고, GitHub Secrets에 AWS 키와 ECR_REGISTRY를 등록하였다. 이후 backend 변경을 main에 push하자 CI가 실제로 이미지를 빌드하여 ECR에 푸시하였고, aws ecr describe-images로 커밋 SHA 태그와 latest 태그가 적재된 것을 직접 확인하였다.

### 2-2. EKS 클러스터 생성 (Terraform)

14주차 Terraform 환경(AWS)에 eks 모듈 호출을 추가하여 EKS 클러스터를 생성하였다. NAT Gateway 미사용 환경이므로 노드를 public 서브넷에 배치하여 IGW 경유로 ECR pull과 control plane join이 가능하게 하였다(비용 절감). Kubernetes 버전은 지원 종료된 1.29 대신 1.33을 사용하였다. 노드 그룹(t3.medium 2대)이 정상적으로 Ready 상태가 되어 클러스터가 가동되었다.

### 2-3. ArgoCD 설치 및 Application 등록

ArgoCD를 Helm으로 argocd 네임스페이스에 설치하였다. GitOps 배포 대상으로 infra/k8s/eks-app(postgres와 redis, backend ECR 이미지)을 구성하고, ArgoCD Application을 다음과 같은 정책으로 등록하였다.

배포 소스(source)는 main 브랜치의 infra/k8s/eks-app 경로로 지정하여 이 경로의 매니페스트를 추적하도록 하였다. 동기화 정책(syncPolicy)에서는 automated 옵션의 prune과 selfHeal을 활성화하여, Git 변경이 자동으로 클러스터에 반영되고 클러스터의 수동 변경(drift)은 Git 기준으로 자동 복구되도록 하였다. 동기화 옵션(syncOptions)에는 CreateNamespace를 true로 두어 네임스페이스를 자동 생성하게 하였고, revisionHistoryLimit을 10으로 설정하여 롤백용 히스토리를 보존하게 하였다.

보안상 민감 정보(DB 접속 정보, SECRET_KEY, 서울버스 키)는 Git에 두지 않고 backend-secret을 kubectl로 별도 생성하였다. 등록 직후 ArgoCD가 자동 동기화하여 Synced 및 Healthy 상태(pod 4개 Running)가 되었다.

### 2-4. GitOps 자동 배포 및 롤백 검증

세 가지 시나리오로 GitOps 동작을 검증하였다.

첫째, 자동 배포 시나리오에서는 app.yaml의 backend replicas를 2에서 3으로 변경하여 push하자, 약 20초 내에 클러스터에 자동으로 반영되어 pod가 3개로 증가하였다. 둘째, 롤백 시나리오에서는 Git revert로 replicas를 다시 3에서 2로 되돌려 push하자, 마찬가지로 약 20초 내에 자동 복구되어 pod가 2개로 돌아왔다. 셋째, ArgoCD의 배포 히스토리에는 초기 배포, replicas 3, replicas 2의 3개 리비전이 기록되어 UI나 CLI로 이전 리비전 롤백이 가능함을 확인하였다.

이로써 Git이 단일 진실 공급원으로 동작하여, 매니페스트 변경이 곧 배포이고 Git revert가 곧 롤백임을 실증하였다.

### 2-5. Ansible 서버 프로비저닝 자동화

새 서버를 Docker 구동 가능 상태로 초기 설정하는 Playbook을 role 기반으로 작성하면서, Ansible의 핵심 개념을 모두 적용하였다.

Inventory는 inventory.ini로 대상 EC2 그룹과 접속 정보를 정의하였다. Playbook은 playbook.yml로 common role과 docker role을 순차 적용하도록 구성하였다. Role은 시스템 업데이트와 기본 유틸리티를 담당하는 common, Docker Engine과 docker compose를 담당하는 docker로 나누어 재사용 가능한 작업 단위로 분리하였다. Module은 각 task에서 dnf, systemd, user, get_url, command 등 멱등 모듈을 호출하였다. Variable은 vars/main.yml에 패키지 목록과 compose 버전 등 파라미터를 분리하여 관리하였다.

실제 EC2에 적용한 결과 총 71초(목표 10분 대비 대폭 단축)에 ok 13건, changed 3건, failed 0건으로 완료되었으며, 재실행 시 변경이 없으면 멱등하게 통과함을 확인하였다.


## 3. 프로젝트 주차 진행 결과

ECR 적재(14주차 완결)는 CI가 ECR로 푸시한 이미지에 SHA 태그와 latest 태그가 적재된 것을 확인하였다. EKS 클러스터는 Kubernetes 1.33으로 노드 2개가 Ready 상태가 되었다. ArgoCD는 Helm 설치 후 Application이 Synced와 Healthy 상태가 되어 pod 4개가 정상 기동되었다. GitOps 자동 배포는 매니페스트의 replicas를 2에서 3으로 변경해 push하자 약 20초 내 자동 반영되었고, 롤백은 Git revert로 3에서 2로 되돌리자 약 20초 내 자동 복구되었으며 히스토리 3개 리비전이 기록되었다. Ansible 프로비저닝은 EC2 초기 설정을 71초에 완료하고 멱등성을 확인하였다.

GitHub: https://github.com/ParkSeongGeun/dream_semester_2026_1


## 4. 기타 (문제점, 해결방법, 자기평가)

### 4-1. 문제점 및 해결방법

EKS 생성 시 unsupported version 1.29 오류가 발생하였다. Kubernetes 1.29가 EKS 지원 종료되었기 때문이며, 지원 버전을 조회한 뒤 1.33으로 변경하여 해결하였다.

노드가 인터넷에 접근하지 못할 우려가 있었다. 노드가 private 서브넷에 배치되는데 NAT Gateway가 없는 환경이었기 때문이며, 노드를 public 서브넷에 배치하여 IGW를 경유하도록 하여 해결하였다.

Ansible 실행이 yaml callback 오류로 실패하였다. community.general.yaml callback 플러그인이 제거되었기 때문이며, result_format을 yaml로 교체하여 해결하였다.

Ansible 패키지 설치가 충돌하였다. Amazon Linux 2023은 curl-minimal이 기본이라 curl 설치가 충돌하였기 때문이며, common_packages에서 curl을 제외하여 해결하였다.

backend pod가 초기에 재시작되었다. postgres가 준비되기 전에 alembic 마이그레이션을 시도했기 때문이며, readinessProbe와 자동 재시작으로 postgres 준비 후 자동 정상화되었다.

### 4-2. 자기평가

ArgoCD를 통해 GitOps의 핵심 원리를 실제로 체감하였다. 기존 CD(14주차 EC2 SSH 배포)는 푸시(push) 기반으로 외부에서 클러스터에 명령을 내리는 방식이었다면, ArgoCD는 풀(pull) 기반으로 클러스터 내 컨트롤러가 Git을 지속 관찰하여 스스로 동기화한다. 매니페스트 변경이 곧 배포, Git revert가 곧 롤백이 되는 선언적 운영을 직접 검증하면서, 클러스터 상태가 Git에 항상 수렴(self-heal)하는 GitOps의 강점을 이해하였다.

Ansible에서는 명령형 셸 스크립트(14주차 user-data)와 달리, 멱등성을 갖춘 선언적 프로비저닝의 장점을 확인하였다. 동일 Playbook을 이미 설정된 서버에 재실행해도 변경이 없으면 안전하게 통과하므로, 서버 수가 늘어도 동일 환경을 일관되게 재현할 수 있다.

또한 14주차 미완료였던 ECR 적재를 완결하여, CI가 빌드한 이미지가 레지스트리에 보관되고 이를 EKS가 pull하여 ArgoCD로 배포하는, CI에서 레지스트리를 거쳐 CD로 이어지는 전체 파이프라인을 하나로 연결하였다.

아쉬운 점은 EKS와 ArgoCD가 시간당 과금되므로 상시 운영보다는 실습 후 terraform destroy로 환경을 정리해야 한다는 점이다. 또한 GitHub Webhook을 ArgoCD에 연동하면 폴링 없이 즉시 동기화가 가능하나, 이번에는 hard refresh로 동기화를 트리거하여 검증하였다.
