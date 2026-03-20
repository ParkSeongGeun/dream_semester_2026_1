"""
서울시 버스 API 서비스

서울시 공공데이터 버스 API와 통신하는 서비스
"""

import httpx
from typing import Any

from app.core.config import settings


class SeoulBusAPIService:
    """서울시 버스 API 클라이언트"""

    def __init__(self):
        self.base_url = settings.seoul_bus_api_base_url
        self.api_key = settings.seoul_bus_api_key
        self.timeout = settings.seoul_bus_api_timeout
        self.max_retries = settings.seoul_bus_api_max_retries

    async def get_station_arrival_info(self, ars_id: str) -> dict[str, Any]:
        """
        정류장 버스 도착 정보 조회

        Args:
            ars_id: 정류장 고유번호 (예: "01234")

        Returns:
            dict: 서울시 API 응답 데이터

        Raises:
            httpx.HTTPError: API 호출 실패
        """
        url = f"{self.base_url}/stationinfo/getStationByUid"
        params = {
            "ServiceKey": self.api_key,
            "arsId": ars_id,
            "resultType": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    if attempt == self.max_retries - 1:
                        raise
                    # 재시도
                    continue

        raise httpx.HTTPError("Max retries exceeded")

    async def get_stations_by_position(
        self,
        latitude: float,
        longitude: float,
        radius: int = 100,
    ) -> dict[str, Any]:
        """
        위치 기반 정류장 조회

        Args:
            latitude: 위도
            longitude: 경도
            radius: 반경(m)

        Returns:
            dict: 서울시 API 응답 데이터

        Raises:
            httpx.HTTPError: API 호출 실패
        """
        url = f"{self.base_url}/stationinfo/getStationByPos"
        params = {
            "ServiceKey": self.api_key,
            "tmX": longitude,
            "tmY": latitude,
            "radius": radius,
            "resultType": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_route_info(self, route_name: str) -> dict[str, Any]:
        """
        버스 노선 정보 조회

        Args:
            route_name: 버스 노선명 (예: "721")

        Returns:
            dict: 서울시 API 응답 데이터

        Raises:
            httpx.HTTPError: API 호출 실패
        """
        url = f"{self.base_url}/businfo/getBusRouteList"
        params = {
            "ServiceKey": self.api_key,
            "strSrch": route_name,
            "resultType": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def check_api_health(self) -> bool:
        """
        서울시 버스 API 연결 상태 확인

        Returns:
            bool: API 연결 가능 여부
        """
        try:
            # 테스트용 ARS ID로 간단한 조회
            url = f"{self.base_url}/stationinfo/getStationByUid"
            params = {
                "ServiceKey": self.api_key,
                "arsId": "01234",
                "resultType": "json",
            }

            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(url, params=params)
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def parse_bus_route_type(route_type_code: str) -> str:
        """
        버스 노선 유형 코드를 한글로 변환

        Args:
            route_type_code: 노선 유형 코드 ("1" ~ "7")

        Returns:
            str: 노선 유형 (한글)
        """
        route_type_map = {
            "1": "공항",
            "2": "마을",
            "3": "간선",
            "4": "지선",
            "5": "순환",
            "6": "광역",
            "7": "인천",
        }
        return route_type_map.get(route_type_code, "기타")

    @staticmethod
    def parse_congestion(congestion_code: str) -> str:
        """
        혼잡도 코드를 영문으로 변환

        Args:
            congestion_code: 혼잡도 코드 ("3" ~ "5")

        Returns:
            str: 혼잡도 (영문)
        """
        congestion_map = {
            "3": "empty",
            "4": "normal",
            "5": "crowded",
        }
        return congestion_map.get(congestion_code, "unknown")

    def parse_arrival_info(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        서울시 API 응답을 파싱하여 정제된 데이터로 변환

        Args:
            raw_data: 서울시 API 응답 데이터

        Returns:
            list[dict]: 정제된 버스 도착 정보 목록
        """
        arrivals = []

        # 응답 구조 확인
        msg_body = raw_data.get("msgBody", {})
        if msg_body is None:
            return arrivals  # msgBody가 None이면 빈 리스트 반환

        item_list = msg_body.get("itemList", [])

        # 단일 항목인 경우 리스트로 변환
        if isinstance(item_list, dict):
            item_list = [item_list]

        for item in item_list:
            arrival = {
                "route_name": item.get("rtNm", ""),
                "route_type": self.parse_bus_route_type(
                    item.get("busRouteType", "")
                ),
                "arrival_message": item.get("arrmsg1", "도착 정보 없음"),
                "direction": item.get("stNm", ""),
                "congestion": self.parse_congestion(item.get("congestion", "")),
                "is_full": item.get("full1", "0") == "1",
                "is_last_bus": item.get("mkTm", "0") == "1",
                "bus_type": item.get("busRouteType", ""),
            }
            arrivals.append(arrival)

        return arrivals


# 서비스 인스턴스 (싱글톤)
seoul_bus_service = SeoulBusAPIService()
