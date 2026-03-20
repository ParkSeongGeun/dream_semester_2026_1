"""
Seoul Bus API Service 단위 테스트

서울시 버스 API 서비스의 파싱 로직을 테스트합니다.
"""

import pytest
from app.services.seoul_bus_api import SeoulBusAPIService


class TestSeoulBusAPIService:
    """Seoul Bus API Service 테스트"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.service = SeoulBusAPIService()

    def test_parse_bus_route_type_gangseon(self):
        """버스 노선 유형 파싱 - 간선"""
        result = self.service.parse_bus_route_type("3")
        assert result == "간선"

    def test_parse_bus_route_type_jiseon(self):
        """버스 노선 유형 파싱 - 지선"""
        result = self.service.parse_bus_route_type("4")
        assert result == "지선"

    def test_parse_bus_route_type_gongHang(self):
        """버스 노선 유형 파싱 - 공항"""
        result = self.service.parse_bus_route_type("1")
        assert result == "공항"

    def test_parse_bus_route_type_maeul(self):
        """버스 노선 유형 파싱 - 마을"""
        result = self.service.parse_bus_route_type("2")
        assert result == "마을"

    def test_parse_bus_route_type_gwangyeok(self):
        """버스 노선 유형 파싱 - 광역"""
        result = self.service.parse_bus_route_type("6")
        assert result == "광역"

    def test_parse_bus_route_type_unknown(self):
        """버스 노선 유형 파싱 - 알 수 없음"""
        result = self.service.parse_bus_route_type("9")
        assert result == "기타"

    def test_parse_congestion_empty(self):
        """혼잡도 파싱 - 여유"""
        result = self.service.parse_congestion("3")
        assert result == "empty"

    def test_parse_congestion_normal(self):
        """혼잡도 파싱 - 보통"""
        result = self.service.parse_congestion("4")
        assert result == "normal"

    def test_parse_congestion_crowded(self):
        """혼잡도 파싱 - 혼잡"""
        result = self.service.parse_congestion("5")
        assert result == "crowded"

    def test_parse_congestion_unknown(self):
        """혼잡도 파싱 - 알 수 없음"""
        result = self.service.parse_congestion("0")
        assert result == "unknown"

    def test_parse_arrival_info_success(self, mock_seoul_api_success):
        """버스 도착 정보 파싱 - 성공"""
        result = self.service.parse_arrival_info(mock_seoul_api_success)

        assert len(result) == 2

        # 첫 번째 버스
        assert result[0]["route_name"] == "721"
        assert result[0]["route_type"] == "간선"
        assert result[0]["arrival_message"] == "2분후[2번째 전]"
        assert result[0]["congestion"] == "empty"
        assert result[0]["is_full"] is False
        assert result[0]["is_last_bus"] is False

        # 두 번째 버스
        assert result[1]["route_name"] == "2012"
        assert result[1]["route_type"] == "지선"
        assert result[1]["arrival_message"] == "5분후[5번째 전]"
        assert result[1]["congestion"] == "normal"

    def test_parse_arrival_info_no_data(self, mock_seoul_api_no_data):
        """버스 도착 정보 파싱 - 데이터 없음"""
        result = self.service.parse_arrival_info(mock_seoul_api_no_data)
        assert len(result) == 0

    def test_parse_arrival_info_empty_itemlist(self):
        """버스 도착 정보 파싱 - 빈 itemList"""
        mock_data = {
            "msgHeader": {"headerCd": "0"},
            "msgBody": {"itemList": []},
        }
        result = self.service.parse_arrival_info(mock_data)
        assert len(result) == 0

    def test_parse_arrival_info_single_item(self):
        """버스 도착 정보 파싱 - 단일 항목 (dict)"""
        mock_data = {
            "msgHeader": {"headerCd": "0"},
            "msgBody": {
                "itemList": {
                    "rtNm": "721",
                    "busRouteType": "3",
                    "arrmsg1": "곧 도착",
                    "stNm": "신설동",
                    "congestion": "3",
                    "full1": "0",
                    "mkTm": "0",
                }
            },
        }
        result = self.service.parse_arrival_info(mock_data)
        assert len(result) == 1
        assert result[0]["route_name"] == "721"


class TestSeoulBusAPIServiceValidation:
    """Seoul Bus API Service 입력 검증 테스트"""

    def setup_method(self):
        self.service = SeoulBusAPIService()

    def test_parse_bus_route_type_with_none(self):
        """None 값 처리"""
        result = self.service.parse_bus_route_type(None)
        assert result == "기타"

    def test_parse_bus_route_type_with_empty_string(self):
        """빈 문자열 처리"""
        result = self.service.parse_bus_route_type("")
        assert result == "기타"

    def test_parse_congestion_with_none(self):
        """None 값 처리"""
        result = self.service.parse_congestion(None)
        assert result == "unknown"

    def test_parse_congestion_with_empty_string(self):
        """빈 문자열 처리"""
        result = self.service.parse_congestion("")
        assert result == "unknown"
