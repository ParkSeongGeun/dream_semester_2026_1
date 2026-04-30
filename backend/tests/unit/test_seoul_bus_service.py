"""
Seoul Bus API Service 단위 테스트

iOS 프론트엔드(ComfortableMove) 호환 응답 정규화 로직 검증.
응답 필드명은 iOS 모델(BusArrivalItem, StationItem) 과 동일하게 유지되어야 함.
"""

from app.services.seoul_bus_api import SeoulBusAPIService


class TestNormalizeArrivalResponse:
    """도착정보 응답 정규화 — iOS BusArrivalResponse 형식 호환"""

    def setup_method(self):
        self.service = SeoulBusAPIService()

    def test_normalize_basic_list(self):
        raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": "1"},
            "msgBody": {
                "itemList": [
                    {
                        "rtNm": "721",
                        "arrmsg1": "2분후[2번째 전]",
                        "adirection": "신설동",
                        "routeType": "3",
                        "isFullFlag1": "0",
                        "isLast1": "0",
                        "congestion1": "3",
                    }
                ]
            },
        }
        out = self.service.normalize_arrival_response(raw)
        assert out["msgHeader"]["headerCd"] == "0"
        assert out["msgHeader"]["itemCount"] == 1  # int 로 변환
        assert len(out["msgBody"]["itemList"]) == 1
        item = out["msgBody"]["itemList"][0]
        assert item["rtNm"] == "721"
        assert item["arrmsg1"] == "2분후[2번째 전]"
        assert item["adirection"] == "신설동"
        assert item["routeType"] == "3"
        assert item["congestion1"] == "3"

    def test_normalize_dict_itemlist_to_list(self):
        """단일 항목이 dict 로 오는 경우 list 로 변환"""
        raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": {
                    "rtNm": "721",
                    "arrmsg1": "곧 도착",
                    "routeType": "3",
                }
            },
        }
        out = self.service.normalize_arrival_response(raw)
        assert isinstance(out["msgBody"]["itemList"], list)
        assert out["msgBody"]["itemList"][0]["rtNm"] == "721"

    def test_normalize_none_itemlist_becomes_empty(self):
        raw = {
            "msgHeader": {"headerCd": "4", "headerMsg": "결과가 없습니다.", "itemCount": 0},
            "msgBody": {"itemList": None},
        }
        out = self.service.normalize_arrival_response(raw)
        assert out["msgBody"]["itemList"] == []

    def test_normalize_missing_msgbody(self):
        raw = {"msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 0}}
        out = self.service.normalize_arrival_response(raw)
        assert out["msgBody"]["itemList"] == []

    def test_congestion_falls_back_to_congestion_field(self):
        """congestion1 미존재 시 congestion 필드를 폴백으로 사용"""
        raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {"rtNm": "721", "routeType": "3", "congestion": "5"}
                ]
            },
        }
        out = self.service.normalize_arrival_response(raw)
        assert out["msgBody"]["itemList"][0]["congestion1"] == "5"

    def test_normalize_keeps_ios_field_names(self):
        """iOS 모델 필드명만 응답에 노출되어야 함 (한글 변환 없음)"""
        raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {
                        "rtNm": "721",
                        "arrmsg1": "2분후",
                        "adirection": "강남",
                        "routeType": "3",
                        "isFullFlag1": "1",
                        "isLast1": "0",
                        "congestion1": "4",
                    }
                ]
            },
        }
        out = self.service.normalize_arrival_response(raw)
        item = out["msgBody"]["itemList"][0]
        # 원본 키만 유지, 변환된 키는 없음
        assert set(item.keys()) == {
            "rtNm", "arrmsg1", "adirection", "routeType",
            "isFullFlag1", "isLast1", "congestion1",
        }


class TestNormalizeStationResponse:
    """정류소 조회 응답 정규화 — iOS StationByPosResponse 형식 호환"""

    def setup_method(self):
        self.service = SeoulBusAPIService()

    def test_normalize_station_basic(self):
        raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {
                        "stationId": "100000001",
                        "stationNm": "서울역",
                        "arsId": "02001",
                        "gpsX": "126.9707",
                        "gpsY": "37.5547",
                        "dist": "42",
                        "stationTp": "0",
                    }
                ]
            },
        }
        out = self.service.normalize_station_response(raw)
        assert out["msgHeader"]["itemCount"] == 1
        item = out["msgBody"]["itemList"][0]
        assert item["stationId"] == "100000001"
        assert item["stationNm"] == "서울역"
        assert item["arsId"] == "02001"
        assert item["gpsX"] == "126.9707"
        assert item["gpsY"] == "37.5547"

    def test_normalize_station_empty(self):
        raw = {
            "msgHeader": {"headerCd": "4", "headerMsg": "결과가 없습니다.", "itemCount": 0},
            "msgBody": {"itemList": None},
        }
        out = self.service.normalize_station_response(raw)
        assert out["msgBody"]["itemList"] == []

    def test_normalize_station_keeps_ios_field_names(self):
        raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {
                        "stationId": "1",
                        "stationNm": "테스트",
                        "arsId": "00001",
                        "gpsX": "126.0",
                        "gpsY": "37.0",
                        "dist": "10",
                        "stationTp": "0",
                    }
                ]
            },
        }
        out = self.service.normalize_station_response(raw)
        item = out["msgBody"]["itemList"][0]
        assert set(item.keys()) == {
            "stationId", "stationNm", "arsId", "gpsX", "gpsY", "dist", "stationTp",
        }
