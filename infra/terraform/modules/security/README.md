# Security Module

3개의 Security Group 생성: ALB, EC2, RDS. 최소 권한 원칙 적용.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 이름 prefix |
| `vpc_id` | string | VPC ID |
| `my_ip` | string | SSH 허용 CIDR (예: `1.2.3.4/32`) |

## 출력

| 출력 | 설명 |
|------|------|
| `alb_sg_id` | ALB SG ID |
| `ec2_sg_id` | EC2 SG ID |
| `rds_sg_id` | RDS SG ID |

## 보안 규칙

- **ALB**: 0.0.0.0/0 → 80, 443
- **EC2**: my_ip → 22 (SSH), ALB SG → 8000 (API)
- **RDS**: EC2 SG → 5432 (PostgreSQL)
