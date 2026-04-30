# Storage Module

S3 버킷 + 버전 관리 + 암호화 + 퍼블릭 액세스 차단 + CORS.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `s3_bucket_name` | string | 버킷 이름 (전역 고유) |

## 출력

| 출력 | 설명 |
|------|------|
| `bucket_name` | 버킷 이름 |
| `bucket_arn` | 버킷 ARN |

## 설계 노트

- AES256 SSE 활성
- 모든 퍼블릭 ACL/Policy 차단
- CORS: GET/PUT/POST 허용 (iOS 클라이언트 업로드용)
