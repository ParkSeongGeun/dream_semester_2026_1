# Ingress Module

Application Load Balancer + Target Group + HTTPS Listener + HTTP→HTTPS 리다이렉트.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 이름 prefix |
| `vpc_id` | string | VPC ID |
| `public_subnet_ids` | list(string) | ALB 배치 서브넷 (2개 이상) |
| `alb_sg_id` | string | ALB SG ID |
| `instance_id` | string | 백엔드 EC2 ID |
| `certificate_arn` | string | ACM 인증서 ARN |

## 출력

| 출력 | 설명 |
|------|------|
| `alb_dns_name` | ALB DNS |
| `alb_zone_id` | ALB Hosted Zone ID |
| `alb_arn_suffix` | CloudWatch 차원용 ARN suffix |
| `target_group_arn_suffix` | TG ARN suffix |

## 설계 노트

- 헬스체크: `GET /api/v1/health` (8000 포트)
- TLS: 1.2/1.3 (`ELBSecurityPolicy-TLS13-1-2-2021-06`)
- HTTP(80) → HTTPS(443) 301 리다이렉트
