# 보안 가이드

## ⚠️ 중요: 민감한 정보 관리

### 환경 변수 파일

**절대 커밋하지 말 것**:
- `.env` - 실제 API 키와 비밀번호 포함
- `.env.local` - 로컬 환경별 설정

**커밋해도 되는 파일**:
- `.env.example` - 템플릿만 포함 (실제 값 없음)

### 현재 .gitignore 설정

```gitignore
.env
.env.local
```

✅ `.env` 파일은 이미 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.

---

## 🔐 민감한 정보 목록

### 1. 서울시 버스 API 키

**위치**: `.env` 파일의 `SEOUL_BUS_API_KEY`

**주의사항**:
- 공개 저장소에 절대 업로드 금지
- API 키 노출 시 즉시 재발급 필요
- 서울시 공공데이터 포털에서 재발급 가능

**발급 방법**:
1. [서울 열린데이터 광장](https://data.seoul.go.kr/) 접속
2. 회원가입 및 로그인
3. 버스도착정보조회 API 신청
4. 발급받은 키를 `.env` 파일에 설정

### 2. 데이터베이스 비밀번호

**위치**: 
- `.env` 파일의 `DATABASE_URL`
- `docker-compose.yml` (환경 변수로 주입)

**권장사항**:
- 개발: 간단한 비밀번호 사용 가능
- 프로덕션: 복잡한 비밀번호 필수 (16자 이상, 특수문자 포함)

### 3. Redis 연결 정보

**위치**: `.env` 파일의 `REDIS_URL`

**주의사항**:
- 프로덕션 환경에서는 Redis에 비밀번호 설정 필수
- 외부 접근 차단 (방화벽 설정)

---

## 📝 설정 방법

### 1. 초기 설정 (최초 1회)

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

### 2. 환경 변수 설정

`.env` 파일에서 다음 값들을 실제 값으로 변경:

```env
# 서울시 버스 API 키 (필수)
SEOUL_BUS_API_KEY=your_actual_api_key_here

# 데이터베이스 비밀번호 (프로덕션 환경에서는 강력한 비밀번호로 변경)
POSTGRES_PASSWORD=your_secure_password_here
```

---

## ✅ 보안 체크리스트

### Git 커밋 전 확인사항

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] 문서 파일에 실제 API 키가 포함되어 있지 않은가?
- [ ] `docker-compose.yml`에 하드코딩된 비밀번호가 없는가?
- [ ] 코드에 API 키나 비밀번호가 하드코딩되어 있지 않은가?

### 이미 수정 완료된 사항 ✅

- ✅ `.env.example` 파일 생성 (템플릿만 포함)
- ✅ `DEVELOPMENT_GUIDE.md`에서 실제 API 키 제거
- ✅ `SEOUL_BUS_API_ANALYSIS.md`에서 실제 API 키 제거
- ✅ `docker-compose.yml`에서 환경 변수 사용으로 변경

---

## 🚨 API 키 노출 시 대응 방법

만약 실수로 API 키를 공개 저장소에 커밋한 경우:

### 1. 즉시 API 키 재발급

```bash
# 서울시 공공데이터 포털에서 기존 키 삭제 및 재발급
```

### 2. Git 히스토리에서 제거 (선택사항)

```bash
# BFG Repo-Cleaner 사용 (권장)
bfg --replace-text sensitive.txt

# 또는 git filter-branch 사용
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

### 3. 강제 푸시

```bash
git push origin --force --all
```

⚠️ **주의**: 협업 중인 프로젝트에서는 팀원들과 상의 후 진행

---

## 🔒 프로덕션 배포 시 추가 보안 사항

### 1. 환경 변수 관리

**AWS Secrets Manager / Parameter Store 사용**:
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

### 2. API 키 로테이션

- 정기적으로 API 키 변경 (3~6개월마다)
- 키 변경 시 무중단 배포 전략 사용

### 3. 접근 제어

- IP 화이트리스트 설정
- VPC 내부에서만 접근 가능하도록 제한

### 4. 로깅 주의사항

```python
# ❌ 나쁜 예
logger.info(f"API Key: {api_key}")

# ✅ 좋은 예
logger.info("API request completed")
```

---

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Git Secret 관리 베스트 프랙티스](https://git-secret.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

---

**작성일**: 2026-03-18
**최종 수정**: 2026-03-18
