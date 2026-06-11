필수 목표
목표 (500자 이내)
15주차는 ArgoCD로 GitOps 기반 CD를 구현하고 Ansible로 서버 프로비저닝을 자동화한다. Git 매니페스트가 단일 진실 공급원이 되어 변경 시 ArgoCD가 자동으로 배포하고 롤백하는 구조를 완성한다. Inventory와 Playbook, Role, Module, Variable 개념을 Playbook에 적용하여 새 서버를 10분 이내에 초기 설정한다. 14주차에 미완료였던 ECR 이미지 적재 검증도 완결한다. 설정 작성에 그치지 않고 EKS를 실제 생성하여 ArgoCD의 자동 배포와 롤백, Ansible 프로비저닝을 직접 검증하는 것을 핵심 목표로 한다.


필수 진행내용
진행내용 (500자 이내)
Terraform에 eks 모듈 호출을 추가하여 EKS를 생성하였다. 쿠버네티스 1.33을 사용하고 NAT 없는 환경이라 노드를 public 서브넷에 배치하였다. ArgoCD를 Helm으로 설치하고 postgres와 redis, backend(ECR 이미지) 매니페스트를 GitOps 대상으로 구성하였다. Application에 자동 동기화와 selfHeal, 롤백 히스토리를 설정하니 즉시 Synced와 Healthy 상태가 되었다. backend replicas를 변경해 push하자 자동 배포되고 Git revert로 롤백되는 것을 확인하였다. Ansible은 common과 docker role로 Playbook을 작성해 EC2를 초기 설정하였다. 14주차 ECR은 Terraform 리포 생성과 Secrets 등록으로 CI push를 활성화하였다.


필수 진행결과
진행결과 (500자 이내)
ECR에 커밋 SHA와 latest 태그가 적재됨을 직접 확인하였다. EKS 노드 2개가 Ready 상태가 되었고 ArgoCD Application이 Synced와 Healthy로 pod 4개가 기동되었다. 매니페스트의 replicas를 2에서 3으로 변경해 push하자 약 20초 내에 자동 배포되었고, Git revert로 3에서 2로 되돌리자 약 20초 내에 자동 복구되었다. 배포 히스토리 3개 리비전으로 롤백 추적이 가능하다. Ansible은 EC2 초기 설정을 71초에 완료하였고 재실행 시 멱등하게 통과하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
EKS는 쿠버네티스 1.29 지원 종료로 1.33으로 변경하였고, NAT 없는 환경에서 노드를 public 서브넷에 배치하였다. Ansible은 제거된 yaml callback을 result_format으로 교체하고 Amazon Linux 2023의 curl 충돌을 제외하여 해결하였다. 자기평가로는 외부에서 명령하는 push 기반 배포와 달리, 클러스터 내 컨트롤러가 Git을 관찰해 스스로 동기화하는 pull 기반 GitOps의 강점을 체감하였다. CI가 빌드한 이미지가 ECR에 보관되고 EKS가 pull하여 ArgoCD로 배포되는 전체 파이프라인을 하나로 연결하였다. 실습 후에는 비용상 terraform destroy로 환경 정리가 필요하다.
