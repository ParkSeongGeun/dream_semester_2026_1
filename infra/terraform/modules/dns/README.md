# DNS Module

Route53 (기존 Hosted Zone 참조) + ACM 인증서 + DNS 검증 + ALB A 레코드.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 이름 prefix |
| `domain_name` | string | 도메인 (예: `comfortablemove.com`) |
| `alb_dns_name` | string | ALB DNS (alias) |
| `alb_zone_id` | string | ALB Zone ID (alias) |

## 출력

| 출력 | 설명 |
|------|------|
| `nameservers` | Route53 네임서버 목록 |
| `certificate_arn` | 검증 완료된 ACM 인증서 ARN |
| `zone_id` | Hosted Zone ID |

## 사전 조건

- 도메인이 이미 Route53 Hosted Zone 으로 등록되어 있어야 함 (`data.aws_route53_zone`)
- `*.<domain>` SAN 자동 포함
