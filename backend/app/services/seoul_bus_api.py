"""
서울시 버스 API 서비스

서울시 공공데이터 버스 API와 통신하는 서비스. 응답을 iOS 프론트엔드의 모델과
호환되는 형식으로 그대로 노출(passthrough)하여 클라이언트가 동일한 디코더를
서울 API와 백엔드 양쪽에 사용할 수 있도록 한다.
"""

from typing import Any

import httpx

from app.core.config import settings


class SeoulBusAPIService:
    """서울시 버스 API 클라이언트"""

    def __init__(self):
        self.base_url = settings.seoul_bus_api_base_url
        self.api_key = settings.seoul_bus_api_key
        self.timeout = settings.seoul_bus_api_timeout
        self.max_retries = settings.seoul_bus_api_max_retries

    async def get_station_arrival_info(self, ars_id: str) -> dict[str, Any]:
        """정류장 버스 도착 정보 조회 (getStationByUid)"""
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
                except httpx.HTTPError:
                    if attempt == self.max_retries - 1:
                        raise
                    continue

        raise httpx.HTTPError("Max retries exceeded")

    async def get_stations_by_position(
        self,
        latitude: float,
        longitude: float,
        radius: int = 100,
    ) -> dict[str, Any]:
        """위치 기반 정류장 조회 (getStationByPos)"""
        url = f"{self.base_url}/stationinfo/getStationByPos"
        params = {
            "ServiceKey": self.api_key,
            "tmX": longitude,  # iOS BusStopService 와 동일하게 lon=tmX, lat=tmY
            "tmY": latitude,
            "radius": radius,
            "resultType": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def check_api_health(self) -> bool:
        """서울시 버스 API 연결 상태 확인"""
        try:
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

    # =============================================================
    # iOS 호환 응답 정규화
    # =============================================================
    @staticmethod
    def _normalize_item_list(raw: dict[str, Any]) -> dict[str, Any]:
        """
        서울 API 응답을 iOS 디코더가 그대로 받을 수 있도록 정규화.
          - msgBody.itemList: dict 단일항목 → list 로 변환, None → []
          - msgHeader.itemCount: 실제 itemList 길이로 보정 (서울 API 가 0 으로
            보내는 quirk 가 있음 — 라이브 응답에서 itemCount=0 이지만
            itemList 는 24개 같은 케이스 관찰)
        필드명은 서울 API 원본을 유지(rtNm, arrmsg1 등) — iOS 모델이 동일 키 사용.
        """
        msg_header = raw.get("msgHeader") or {}

        msg_body = raw.get("msgBody") or {}
        item_list = msg_body.get("itemList")
        if item_list is None:
            item_list = []
        elif isinstance(item_list, dict):
            item_list = [item_list]

        normalized_header = {
            "headerCd": str(msg_header.get("headerCd", "")),
            "headerMsg": str(msg_header.get("headerMsg", "")),
            "itemCount": len(item_list),
        }

        return {
            "msgHeader": normalized_header,
            "msgBody": {"itemList": item_list},
        }

    @classmethod
    def normalize_arrival_response(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """도착정보 응답을 iOS BusArrivalResponse 형식으로 정규화"""
        normalized = cls._normalize_item_list(raw)
        # 도착정보에서만 필요한 필드만 골라 클라이언트 모델과 정확히 매칭
        cleaned_items = []
        for item in normalized["msgBody"]["itemList"]:
            cleaned_items.append(
                {
                    "rtNm": str(item.get("rtNm", "")),
                    "arrmsg1": item.get("arrmsg1"),
                    "adirection": item.get("adirection"),
                    "routeType": str(item.get("routeType", "")),
                    "isFullFlag1": item.get("isFullFlag1"),
                    "isLast1": item.get("isLast1"),
                    # 일부 응답은 congestion1 미존재 → congestion 키도 폴백으로 본다
                    "congestion1": item.get("congestion1") or item.get("congestion"),
                }
            )
        normalized["msgBody"]["itemList"] = cleaned_items
        return normalized

    @classmethod
    def normalize_station_response(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """정류소 조회 응답을 iOS StationByPosResponse 형식으로 정규화"""
        normalized = cls._normalize_item_list(raw)
        cleaned_items = []
        for item in normalized["msgBody"]["itemList"]:
            cleaned_items.append(
                {
                    "stationId": str(item.get("stationId", "")),
                    "stationNm": str(item.get("stationNm", "")),
                    "arsId": str(item.get("arsId", "")),
                    "gpsX": str(item.get("gpsX", "")),
                    "gpsY": str(item.get("gpsY", "")),
                    "dist": str(item.get("dist", "")),
                    "stationTp": str(item.get("stationTp", "")),
                }
            )
        normalized["msgBody"]["itemList"] = cleaned_items
        return normalized


# 서비스 인스턴스 (싱글톤)
seoul_bus_service = SeoulBusAPIService()
