# RDS Module

PostgreSQL 15 RDS 인스턴스, 서브넷 그룹, 파라미터 그룹 생성.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 이름 prefix |
| `db_instance_class` | string | RDS 클래스 (예: `db.t3.micro`) |
| `db_name` | string | 초기 DB 이름 |
| `db_username` | string | 마스터 사용자명 |
| `db_password` | string | 마스터 비밀번호 (sensitive) |
| `db_multi_az` | bool | Multi-AZ 활성 여부 |
| `private_subnet_ids` | list(string) | DB 서브넷 그룹용 |
| `rds_sg_id` | string | RDS Security Group |

## 출력

| 출력 | 설명 |
|------|------|
| `endpoint` | RDS 엔드포인트 (`<host>:5432`) |
| `db_name` | DB 이름 |
| `db_instance_id` | 인스턴스 식별자 |

## 설계 노트

- 스토리지: gp3 20GB, 자동 확장 30GB, 암호화 활성
- 백업: 7일 보관, 최종 스냅샷 생략 (skip_final_snapshot=true)
- 파라미터: `log_statement=all`, `log_min_duration_statement=1000ms`
