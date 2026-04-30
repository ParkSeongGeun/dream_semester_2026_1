# Network Module

VPC, 서브넷(public/private), IGW, NAT Gateway(선택), 라우팅 테이블 생성.

## 입력

| 변수 | 타입 | 설명 |
|------|------|------|
| `project_name` | string | 리소스 이름 prefix |
| `vpc_cidr` | string | VPC CIDR (예: `10.10.0.0/16`) |
| `public_subnet_cidrs` | list(string) | 퍼블릭 서브넷 CIDR (AZ 순서 일치) |
| `private_subnet_cidrs` | list(string) | 프라이빗 서브넷 CIDR |
| `availability_zones` | list(string) | 가용영역 (예: `["ap-northeast-2a", "ap-northeast-2c"]`) |
| `enable_nat_gateway` | bool | NAT GW 생성 여부 (default false) |

## 출력

| 출력 | 설명 |
|------|------|
| `vpc_id` | 생성된 VPC ID |
| `public_subnet_ids` | 퍼블릭 서브넷 ID 리스트 |
| `private_subnet_ids` | 프라이빗 서브넷 ID 리스트 |
| `public_subnet_map` | AZ → 서브넷 ID 매핑 |
| `private_subnet_map` | AZ → 서브넷 ID 매핑 |

## 사용 예

```hcl
module "network" {
  source = "../../modules/network"

  project_name         = "comfortablemove-dev"
  vpc_cidr             = "10.10.0.0/16"
  public_subnet_cidrs  = ["10.10.1.0/24", "10.10.2.0/24"]
  private_subnet_cidrs = ["10.10.11.0/24", "10.10.12.0/24"]
  availability_zones   = ["ap-northeast-2a", "ap-northeast-2c"]
  enable_nat_gateway   = false
}
```

## 설계 노트

- 서브넷은 `for_each` 로 AZ 키 기반 생성 → 인덱스 변경에 안전
- NAT Gateway 는 `count` + `enable_nat_gateway` 로 조건부 생성 (비용 절감)
- 프라이빗 라우팅 테이블은 항상 1개 (NAT 없을 때는 외부 경로 미설정)
