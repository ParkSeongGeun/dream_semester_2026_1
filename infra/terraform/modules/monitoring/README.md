# Monitoring Module

AWS Budgets + CloudWatch Alarms + CloudWatch Dashboard + SNS 알림.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 이름 prefix |
| `aws_region` | string | 리전 |
| `budget_limit` | string | 월간 예산 한도 (USD) |
| `notification_email` | string | 알림 이메일 |
| `instance_id` | string | EC2 ID (CW 차원) |
| `alb_arn_suffix` | string | ALB ARN suffix |
| `target_group_arn_suffix` | string | TG ARN suffix |
| `db_instance_id` | string | RDS ID |

## 출력

| 출력 | 설명 |
|------|------|
| `budget_name` | Budget 이름 |
| `dashboard_name` | CW Dashboard 이름 |
| `sns_topic_arn` | SNS Topic ARN |

## 알람 정의

- EC2 CPU > 80% (5분 평균, 2회 연속)
- ALB 5xx > 10건/5분
- ALB 비정상 호스트 > 0
- RDS CPU > 80%, 여유 스토리지 < 2GB

## 예산 알림 (50%, 80%, 100% 실제 / 100% 예측)
