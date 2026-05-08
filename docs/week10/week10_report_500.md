필수 목표
목표 (500자 이내)
10주차에는 Kubernetes 핵심 개념을 학습하고 로컬 클러스터에 맘편한 이동(ComfortableMove) 백엔드 API를 직접 배포하는 것을 목표로 한다. Control Plane과 Worker Node의 역할, Pod·ReplicaSet·Deployment·Service·ConfigMap·Secret 오브젝트의 책임 분담을 학습한다. Minikube로 로컬 v1.34.0 클러스터를 구성하고 백엔드 API를 Deployment(replicas=3)로 배포하여 셀프힐링과 롤링 업데이트를 직접 검증한다. 매니페스트는 infra/k8s/ 디렉토리에 정리하고 실제 Secret 값은 .gitignore로 커밋을 차단한다. 부수 작업으로 9주차 누락된 iOS device_id 관리·boarding 호출을 보강하고 누적 실패하던 GitHub Actions CI/CD 워크플로를 정상화한다.


필수 진행내용
진행내용 (500자 이내)
Minikube로 클러스터를 띄우고 infra/k8s/에 매니페스트(namespace·configmap·secret·deployment·service·kustomization·README·gitignore)를 작성하였다. Deployment는 replicas=3·RollingUpdate·envFrom·probe·limit, Service는 ClusterIP 80→8000으로 두었다. image load 후 apply -k로 배포하였다. iOS에 DeviceIdentityManager·BoardingRecordService를 추가해 익명 UUID와 /boarding/record fire-and-forget 호출을 구현하고 백엔드 users_devices 자동 upsert로 FK 위반을 방지하였다. CI/CD는 시크릿 가드·paths 정밀화·Literal 확장·conftest 보정·aiosqlite·Redis mock 정정으로 통과시켰다.


필수 진행결과
진행결과 (500자 이내)
파드 3개 모두 1/1 Ready 0 RESTARTS로 안정 동작하며 /api/v1/health에서 database·redis·seoul_bus_api 모두 connected 응답을 확인하였다. kubectl delete pod --force로 파드를 강제 삭제하면 신규 파드가 즉시 생성되어 3/3 상태가 유지되는 self-healing을 직접 관찰하였다. iOS Xcode 빌드 SUCCEEDED, 백엔드 통합 테스트 11/11 PASSED(기존 9+신규 2)를 확인하였다. CI - Test & Lint 1m14s success, CD - Deploy to EC2 6s success(시크릿 미등록 → skip 워닝)로 워크플로 양쪽 통과를 검증하였다. 커밋은 [Chore] Secret 차단·[Feat] 매니페스트·[Docs] README·[Fix] CI/CD 정상화·[Fix] aiosqlite의 의미 단위로 분리하였다.


기타(문제점, 해결방법, 자기평가 등)
기타 (500자 이내)
문제점·해결: 호스트 5432 충돌(네이티브 postgres) → docker network connect로 IP 직접 통신. host.minikube.internal Pod DNS 미반영 → IP 직박. CrashLoopBackOff backoff → rollout restart 리셋. postgres volume 자격증명 잔재 → down -v. 워크플로 누적 실패 → 시크릿 가드·Literal 확장·conftest 보정·aiosqlite·mock 정정의 6단계 수정.
자기평가: 매니페스트 작성으로 K8s 책임 분담을 체화하고 self-healing 검증으로 desired state 모델의 가치를 체감하였다. lsof로 충돌 원인을 좁히며 호스트 OS와 컨테이너 경계 감각을 익혔다. 아쉬운 점은 PostgreSQL/Redis K8s 이전(StatefulSet/PV)과 EC2 실배포 보류이며 다음 주차 과제로 둔다.
