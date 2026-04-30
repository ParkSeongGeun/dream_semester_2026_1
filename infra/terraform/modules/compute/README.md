# Compute Module

EC2 인스턴스 + IAM Role(S3 접근) + Key Pair + Elastic IP 생성. Amazon Linux 2023 AMI 자동 조회.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 이름 prefix |
| `ec2_instance_type` | string | EC2 타입 (예: `t3.micro`, `t3.small`) |
| `ssh_public_key_path` | string | 공개키 파일 경로 (예: `~/.ssh/id_rsa.pub`) |
| `public_subnet_ids` | list(string) | 배치할 퍼블릭 서브넷 |
| `ec2_sg_id` | string | EC2 Security Group ID |
| `s3_bucket_arn` | string | S3 IAM 정책 대상 버킷 ARN |

## 출력

| 출력 | 설명 |
|------|------|
| `instance_id` | EC2 인스턴스 ID |
| `public_ip` | EIP 퍼블릭 IP |

## 설계 노트

- 첫 번째 퍼블릭 서브넷에만 배치 (Single-instance)
- 루트 EBS: 20GB gp3, 암호화 활성
- IAM: S3 GetObject/PutObject/ListBucket 만 허용
- `templates/user-data.sh` 가 부트 시 실행됨
