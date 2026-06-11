# Ansible — 서버 초기 설정 자동화 (15주차)

새 서버(EC2 등)를 **Docker 구동 가능 상태로 자동 프로비저닝**한다. 수작업 SSH 설정을 멱등(idempotent) Playbook으로 대체하여 10분 이내 초기 설정을 목표로 한다.

## 구조 (Ansible 핵심 개념 매핑)

| 개념 | 파일 | 역할 |
|------|------|------|
| **Inventory** | `inventory.ini` | 대상 서버 그룹·접속 정보 |
| **Playbook** | `playbook.yml` | 적용할 role 묶음·실행 순서 |
| **Role** | `roles/common`, `roles/docker` | 재사용 가능한 작업 단위 |
| **Module** | `dnf`, `systemd`, `user`, `get_url` 등 | 각 task가 호출하는 멱등 작업 |
| **Variable** | `roles/*/vars/main.yml` | 패키지 목록·compose 버전 등 파라미터 |

```
ansible/
├── ansible.cfg              # 기본 설정 (inventory, 권한 상승)
├── inventory.ini           # 대상 서버
├── playbook.yml            # common → docker role 순차 적용
└── roles/
    ├── common/             # 시스템 업데이트 + 기본 유틸리티(git, curl, vim ...)
    └── docker/             # Docker Engine + docker compose plugin
```

## 실행

```bash
cd infra/ansible

# 1) 문법 검사
ansible-playbook playbook.yml --syntax-check

# 2) 연결 확인
ansible webservers -m ping

# 3) dry-run (변경 미리보기)
ansible-playbook playbook.yml --check

# 4) 실제 적용
ansible-playbook playbook.yml
```

> `inventory.ini`의 `ansible_host`는 `terraform output ec2_public_ip` 값으로 갱신한다.

## 멱등성

모든 task는 멱등하게 작성되어, 이미 설정된 서버에 재실행해도 변경이 없으면 `changed=0`으로 안전하게 통과한다. 새 서버에는 동일 Playbook 한 번으로 동일 환경이 재현된다.
