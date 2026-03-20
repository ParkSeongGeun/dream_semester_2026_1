## 개요

  ### 데이터베이스 시스템
  - **DBMS**: PostgreSQL 15
  - **문자 인코딩**: UTF-8
  - **타임존**: Asia/Seoul (KST)

  ### 주요 테이블
  1. `users_devices` - iOS 기기 정보
  2. `boarding_records` - 탑승 기록

  ---

  ## 1. users_devices 테이블

  ### 목적
  iOS 기기 정보를 저장하여 향후 사용자 관리 및 통계 분석에 활용합니다.

  ### 테이블 구조

  | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | 설명 |
  |--------|------------|----------|--------|------|
  | `device_id` | UUID | NO | gen_random_uuid() | 기기 고유 ID (Primary Key) |
  | `device_token` | VARCHAR(255) | YES | NULL | iOS 기기 식별자 (선택) |
  | `device_name` | VARCHAR(100) | YES | NULL | 기기 이름 (예: "iPhone 14 Pro") |
  | `os_version` | VARCHAR(20) | YES | NULL | iOS 버전 (예: "iOS 17.2") |
  | `app_version` | VARCHAR(20) | YES | NULL | 앱 버전 (예: "1.2.1") |
  | `is_verified` | BOOLEAN | NO | FALSE | 임산부 인증 여부 |
  | `due_date` | DATE | YES | NULL | 출산 예정일 (임신 기간 추적용) |
  | `sound_enabled` | BOOLEAN | NO | TRUE | 알림음 설정 |
  | `created_at` | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 기기 등록 시간 |
  | `last_active_at` | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 마지막 활동 시간 |

  ### SQL 생성 구문

  ```sql
  CREATE TABLE users_devices (
      -- Primary Key
      device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

      -- Device Information
      device_token VARCHAR(255) UNIQUE,
      device_name VARCHAR(100),
      os_version VARCHAR(20),
      app_version VARCHAR(20),

      -- User Profile
      is_verified BOOLEAN DEFAULT FALSE,
      due_date DATE,

      -- Settings
      sound_enabled BOOLEAN DEFAULT TRUE,

      -- Metadata
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

      -- Constraints
      CONSTRAINT chk_app_version CHECK (app_version ~ '^\d+\.\d+\.\d+$')
  );

  -- Indexes
  CREATE INDEX idx_users_devices_last_active ON users_devices(last_active_at DESC);
  CREATE INDEX idx_users_devices_token ON users_devices(device_token) WHERE device_token IS NOT NULL;

  설계 근거

  1. UUID 사용 이유
    - 보안: 순차적 ID보다 예측 불가능
    - 확장성: 여러 서버에서 생성해도 충돌 없음
  2. device_token이 NULL 허용인 이유
    - 초기에는 익명 사용 허용
    - 나중에 회원가입 기능 추가 시 업데이트
  3. due_date 필드 추가 이유
    - 출산 예정일을 저장하여 임신 기간 추적
    - 임산부 인증 시 is_verified와 함께 활용
    - NULL 허용: 임산부가 아닌 일반 사용자 지원
  4. 인덱스 전략
    - last_active_at: 비활성 사용자 정리 쿼리 최적화
    - device_token: 기기로 사용자 검색 시 성능 향상

  ---
  2. boarding_records 테이블

  목적

  사용자가 배려석 알림을 보낸 모든 기록을 저장합니다.
  - 사용 통계 분석
  - 인기 노선/정류장 파악
  - Bluetooth 전송 성공률 추적

  테이블 구조
  컬럼명: record_id
  데이터 타입: UUID
  NULL 허용: NO
  기본값: gen_random_uuid()
  설명: 기록 고유 ID (Primary Key)
  ────────────────────────────────────────
  컬럼명: device_id
  데이터 타입: UUID
  NULL 허용: YES
  기본값: NULL
  설명: 기기 ID (Foreign Key)
  ────────────────────────────────────────
  컬럼명: route_name
  데이터 타입: VARCHAR(20)
  NULL 허용: NO
  기본값: -
  설명: 버스 노선명 (예: "721", "강동01")
  ────────────────────────────────────────
  컬럼명: route_type
  데이터 타입: VARCHAR(10)
  NULL 허용: YES
  기본값: NULL
  설명: 노선 유형 (간선, 지선 등)
  ────────────────────────────────────────
  컬럼명: bus_device_id
  데이터 타입: VARCHAR(50)
  NULL 허용: YES
  기본값: NULL
  설명: BLE 기기 ID (예: "BF_DREAM_721")
  ────────────────────────────────────────
  컬럼명: station_id
  데이터 타입: VARCHAR(20)
  NULL 허용: YES
  기본값: NULL
  설명: 정류장 ID (서울시 API)
  ────────────────────────────────────────
  컬럼명: station_name
  데이터 타입: VARCHAR(100)
  NULL 허용: YES
  기본값: NULL
  설명: 정류장 이름 (예: "신설동역")
  ────────────────────────────────────────
  컬럼명: ars_id
  데이터 타입: VARCHAR(20)
  NULL 허용: YES
  기본값: NULL
  설명: 정류장 고유번호
  ────────────────────────────────────────
  컬럼명: latitude
  데이터 타입: DECIMAL(10, 7)
  NULL 허용: YES
  기본값: NULL
  설명: 탑승 위치 위도
  ────────────────────────────────────────
  컬럼명: longitude
  데이터 타입: DECIMAL(10, 7)
  NULL 허용: YES
  기본값: NULL
  설명: 탑승 위치 경도
  ────────────────────────────────────────
  컬럼명: sound_enabled
  데이터 타입: BOOLEAN
  NULL 허용: NO
  기본값: TRUE
  설명: 알림음 사용 여부
  ────────────────────────────────────────
  컬럼명: notification_status
  데이터 타입: VARCHAR(20)
  NULL 허용: NO
  기본값: -
  설명: 전송 결과 (success, device_not_found, failure)
  ────────────────────────────────────────
  컬럼명: boarded_at
  데이터 타입: TIMESTAMP WITH TIME ZONE
  NULL 허용: NO
  기본값: CURRENT_TIMESTAMP
  설명: 탑승 시간
  SQL 생성 구문

  CREATE TABLE boarding_records (
      -- Primary Key
      record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

      -- Foreign Key (nullable for anonymous usage)
      device_id UUID REFERENCES users_devices(device_id) ON DELETE SET NULL,

      -- Bus Information
      route_name VARCHAR(20) NOT NULL,
      route_type VARCHAR(10),
      bus_device_id VARCHAR(50),

      -- Station Information
      station_id VARCHAR(20),
      station_name VARCHAR(100),
      ars_id VARCHAR(20),

      -- Location
      latitude DECIMAL(10, 7),
      longitude DECIMAL(10, 7),

      -- Notification Details
      sound_enabled BOOLEAN DEFAULT TRUE,
      notification_status VARCHAR(20) NOT NULL,

      -- Timestamp
      boarded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

      -- Constraints
      CONSTRAINT chk_notification_status
          CHECK (notification_status IN ('success', 'device_not_found', 'failure')),
      CONSTRAINT chk_latitude
          CHECK (latitude BETWEEN -90 AND 90),
      CONSTRAINT chk_longitude
          CHECK (longitude BETWEEN -180 AND 180)
  );

  -- Indexes for analytics
  CREATE INDEX idx_boarding_records_device ON boarding_records(device_id);
  CREATE INDEX idx_boarding_records_route ON boarding_records(route_name);
  CREATE INDEX idx_boarding_records_boarded_at ON boarding_records(boarded_at DESC);
  CREATE INDEX idx_boarding_records_station ON boarding_records(station_id);
  CREATE INDEX idx_boarding_records_status ON boarding_records(notification_status);

  -- Composite index for user history queries
  CREATE INDEX idx_boarding_records_device_date
      ON boarding_records(device_id, boarded_at DESC);

  설계 근거

  1. device_id가 NULL 허용인 이유
    - 익명 사용자도 탑승 기록 저장 가능
    - 기기 삭제해도 기록은 보존 (ON DELETE SET NULL)
  2. 인덱스가 많은 이유
    - 통계 쿼리가 많기 때문 (인기 노선, 정류장 등)
    - 조회 성능 >> 저장 성능 (읽기가 쓰기보다 훨씬 많음)
  3. 복합 인덱스 (device_id, boarded_at)
    - "이 사용자의 최근 탑승 기록" 쿼리 최적화
    - 가장 자주 사용되는 쿼리 패턴

  ---
  3. 테이블 관계도 (ERD)

  관계 설명

  - users_devices 1 : N boarding_records
  - 한 기기는 여러 탑승 기록을 가질 수 있음
  - 탑승 기록은 하나의 기기에만 속함 (또는 NULL)

  Mermaid 다이어그램

  erDiagram
      USERS_DEVICES ||--o{ BOARDING_RECORDS : "has many"

      USERS_DEVICES {
          uuid device_id PK
          varchar device_token UK
          varchar device_name
          varchar os_version
          varchar app_version
          boolean is_verified
          boolean sound_enabled
          timestamp created_at
          timestamp last_active_at
      }

      BOARDING_RECORDS {
          uuid record_id PK
          uuid device_id FK
          varchar route_name
          varchar route_type
          varchar bus_device_id
          varchar station_id
          varchar station_name
          varchar ars_id
          decimal latitude
          decimal longitude
          boolean sound_enabled
          varchar notification_status
          timestamp boarded_at
      }

  ---
  4. 샘플 데이터

  users_devices 샘플

  INSERT INTO users_devices (device_token, device_name, os_version, app_version, sound_enabled)
  VALUES
      ('ABC123XYZ', 'iPhone 14 Pro', 'iOS 17.2', '1.0.0', TRUE),
      ('DEF456UVW', 'iPhone 13', 'iOS 16.5', '1.0.0', FALSE);

  boarding_records 샘플

  INSERT INTO boarding_records (
      device_id,
      route_name,
      route_type,
      bus_device_id,
      station_name,
      ars_id,
      latitude,
      longitude,
      notification_status
  )
  VALUES
      (
          (SELECT device_id FROM users_devices WHERE device_token = 'ABC123XYZ'),
          '721',
          '간선',
          'BF_DREAM_721',
          '신설동역',
          '01234',
          37.575000,
          127.025000,
          'success'
      ),
      (
          (SELECT device_id FROM users_devices WHERE device_token = 'ABC123XYZ'),
          '2012',
          '지선',
          'BF_DREAM_2012',
          '강남역',
          '23288',
          37.497940,
          127.027610,
          'device_not_found'
      );

  ---
  5. 주요 쿼리 예시

  사용자의 최근 탑승 기록 조회

  SELECT
      route_name,
      station_name,
      notification_status,
      boarded_at
  FROM boarding_records
  WHERE device_id = '550e8400-e29b-41d4-a716-446655440000'
  ORDER BY boarded_at DESC
  LIMIT 10;

  인기 노선 Top 10

  SELECT
      route_name,
      route_type,
      COUNT(*) as boarding_count
  FROM boarding_records
  WHERE boarded_at >= NOW() - INTERVAL '30 days'
  GROUP BY route_name, route_type
  ORDER BY boarding_count DESC
  LIMIT 10;

  성공률 계산

  SELECT
      notification_status,
      COUNT(*) as count,
      ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
  FROM boarding_records
  WHERE boarded_at >= NOW() - INTERVAL '7 days'
  GROUP BY notification_status;

  ---
  6. 데이터베이스 초기화 스크립트

  Week 3에서 사용할 전체 초기화 스크립트입니다.

  -- Drop existing tables (개발 환경에서만 사용)
  DROP TABLE IF EXISTS boarding_records CASCADE;
  DROP TABLE IF EXISTS users_devices CASCADE;

  -- Create tables
  -- (위의 CREATE TABLE 구문 참조)

  -- Create indexes
  -- (위의 CREATE INDEX 구문 참조)

  -- Insert sample data (선택)
  -- (위의 INSERT 구문 참조)

  ---
  변경 이력
  ┌────────────┬───────┬──────────────────┐
  │    날짜    │ 버전  │    변경 내용     │
  ├────────────┼───────┼──────────────────┤
  │ 2026-03-08 │ 1.0.0 │ 초기 스키마 설계 │
  └────────────┴───────┴──────────────────┘
  ---

  ### Step 2-2: 작성 확인

  파일을 저장한 후 다음을 확인해보세요:

  1. **파일 경로가 맞는지:**
     ```bash
     ls backend/docs/DATABASE_SCHEMA.md

  2. 내용이 잘 작성되었는지 미리보기
    - VSCode에서 Cmd + Shift + V (Mac) 또는 Ctrl + Shift + V (Windows)

  ---
