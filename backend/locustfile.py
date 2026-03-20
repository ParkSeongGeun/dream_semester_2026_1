"""
부하 테스트 (Load Testing with Locust)

출퇴근 시간에 특정 버스에 대한 요청이 많을 때 문제가 없는지 검증합니다.
- 동시 사용자: 100명
- 시나리오: 버스 도착 정보 조회 집중 테스트
- 캐시 효과 검증 (캐시 히트 vs 미스)
"""

import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner

# 인기 있는 서울 정류장 ARS ID 목록 (테스트용)
POPULAR_STATIONS = [
    "01234",  # 테스트용
    "23288",  # 강남역
    "23189",  # 서울역
    "10002",  # 시청역
]

# 통계 수집을 위한 변수
cache_hits = 0
cache_misses = 0


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작 시 실행"""
    global cache_hits, cache_misses
    cache_hits = 0
    cache_misses = 0
    print("🚀 부하 테스트 시작")
    print(f"📊 테스트 대상: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 시 실행"""
    print("\n" + "=" * 50)
    print("📊 부하 테스트 결과 요약")
    print("=" * 50)
    print(f"🔵 총 캐시 히트: {cache_hits}")
    print(f"🔴 총 캐시 미스: {cache_misses}")

    total = cache_hits + cache_misses
    if total > 0:
        hit_rate = (cache_hits / total) * 100
        print(f"✅ 캐시 히트율: {hit_rate:.2f}%")
        print(f"📈 예상 성능 개선: {hit_rate:.1f}% 요청이 빠른 응답")
    else:
        print("⚠️  캐시 통계 없음")

    print("=" * 50)


class BusUserBehavior(HttpUser):
    """
    버스 이용자 행동 시뮬레이션

    출퇴근 시간에 특정 버스 정류장을 반복적으로 조회하는 패턴
    """

    # 요청 간격: 2~5초 (실제 사용자처럼)
    wait_time = between(2, 5)

    def on_start(self):
        """각 사용자 시작 시 실행"""
        # 각 사용자는 자주 이용하는 정류장 1~2개를 선택
        self.favorite_stations = random.sample(POPULAR_STATIONS, k=random.randint(1, 2))

    @task(5)
    def get_bus_arrivals_favorite(self):
        """자주 이용하는 정류장 조회 (높은 빈도)"""
        ars_id = random.choice(self.favorite_stations)
        self._get_bus_arrivals(ars_id)

    @task(1)
    def get_bus_arrivals_random(self):
        """랜덤 정류장 조회 (낮은 빈도)"""
        ars_id = random.choice(POPULAR_STATIONS)
        self._get_bus_arrivals(ars_id)

    def _get_bus_arrivals(self, ars_id: str):
        """버스 도착 정보 조회 및 캐시 통계 수집"""
        global cache_hits, cache_misses

        with self.client.get(
            f"/api/v1/bus/arrivals?ars_id={ars_id}",
            catch_response=True,
            name="/api/v1/bus/arrivals",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # 캐시 히트 여부 확인
                if data.get("cached"):
                    cache_hits += 1
                else:
                    cache_misses += 1
                response.success()
            elif response.status_code == 404:
                # 404는 정상 (테스트 데이터이므로)
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")

    @task(2)
    def create_boarding_record(self):
        """탑승 기록 저장"""
        data = {
            "route_name": random.choice(["721", "2012", "9403"]),
            "sound_enabled": True,
            "notification_status": random.choice(
                ["success", "device_not_found", "failure"]
            ),
            "latitude": 37.5 + random.uniform(-0.1, 0.1),
            "longitude": 127.0 + random.uniform(-0.1, 0.1),
        }

        with self.client.post(
            "/api/v1/boarding/record",
            json=data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")

    @task(1)
    def health_check(self):
        """헬스체크"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


class PeakHourUser(HttpUser):
    """
    출퇴근 시간대 사용자 시뮬레이션

    더 빠른 요청 간격으로 높은 부하 생성
    """

    wait_time = between(1, 3)  # 더 짧은 간격

    def on_start(self):
        # 특정 정류장에 집중
        self.station = random.choice(POPULAR_STATIONS[:2])

    @task
    def get_bus_arrivals(self):
        """버스 도착 정보 집중 조회"""
        global cache_hits, cache_misses

        with self.client.get(
            f"/api/v1/bus/arrivals?ars_id={self.station}",
            catch_response=True,
            name="/api/v1/bus/arrivals (peak hour)",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("cached"):
                    cache_hits += 1
                else:
                    cache_misses += 1
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
