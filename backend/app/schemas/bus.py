"""
버스 도착 정보 스키마

iOS 프론트엔드 (ComfortableMove)의 모델과 1:1 일치하도록 정의.
필드명/구조는 iOS의 BusArrivalResponse, StationByPosResponse 와 동일하게 유지.
"""

from pydantic import BaseModel, Field


# =============================================================
# 공통 메시지 헤더 (iOS: MsgHeader)
# =============================================================
class MsgHeader(BaseModel):
    """서울시 버스 API 호환 메시지 헤더 (iOS MsgHeader 와 동일)"""

    headerCd: str = Field(..., description="결과 코드 (0=성공, 4=결과없음)")
    headerMsg: str = Field(..., description="결과 메시지")
    itemCount: int = Field(..., description="결과 아이템 수")


# =============================================================
# 버스 도착 정보 (iOS: BusArrivalItem)
# =============================================================
class BusArrivalItem(BaseModel):
    """단일 버스 도착 정보 — iOS BusArrivalItem 과 동일한 필드명/타입"""

    rtNm: str = Field(..., description="노선명", examples=["721"])
    arrmsg1: str | None = Field(default=None, description="첫번째 버스 도착 메시지", examples=["2분후[2번째 전]"])
    adirection: str | None = Field(default=None, description="방향(종점)", examples=["신설동"])
    routeType: str = Field(..., description="노선유형 코드 (3:간선, 4:지선 등)", examples=["3"])
    isFullFlag1: str | None = Field(default=None, description="만차 여부 (0/1)")
    isLast1: str | None = Field(default=None, description="막차 여부 (0/1)")
    congestion1: str | None = Field(
        default=None,
        description="혼잡도 코드 (0/3:여유, 4:보통, 5/6:혼잡)",
    )


class BusArrivalMsgBody(BaseModel):
    """iOS MsgBody — 도착정보용"""

    itemList: list[BusArrivalItem] | None = Field(default=None, description="도착정보 리스트")


class BusArrivalResponse(BaseModel):
    """버스 도착 정보 응답 — iOS BusArrivalResponse 와 동일한 최상위 구조"""

    msgHeader: MsgHeader
    msgBody: BusArrivalMsgBody

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "msgHeader": {"headerCd": "0", "headerMsg": "정상적으로 처리되었습니다.", "itemCount": 1},
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
            ]
        }
    }


# =============================================================
# 정류소 조회 (iOS: StationByPosResponse)
# =============================================================
class StationItem(BaseModel):
    """위치 기반 정류소 아이템 — iOS StationItem 과 동일"""

    stationId: str = Field(..., description="정류소 고유 ID")
    stationNm: str = Field(..., description="정류소명")
    arsId: str = Field(..., description="정류소 번호 (API 호출용)")
    gpsX: str = Field(..., description="정류소 좌표 X (WGS84, 경도)")
    gpsY: str = Field(..., description="정류소 좌표 Y (WGS84, 위도)")
    dist: str = Field(..., description="거리 (m)")
    stationTp: str = Field(..., description="정류소 타입 (0:공용, 1:일반형, 7:마을 등)")


class StationMsgBody(BaseModel):
    """iOS StationMsgBody"""

    itemList: list[StationItem] | None = Field(default=None, description="정류소 리스트")


class StationByPosResponse(BaseModel):
    """위치 기반 정류소 조회 응답 — iOS StationByPosResponse 와 동일"""

    msgHeader: MsgHeader
    msgBody: StationMsgBody

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
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
            ]
        }
    }


# =============================================================
# 에러 응답
# =============================================================
class ErrorResponse(BaseModel):
    """에러 응답 (FastAPI HTTPException detail)"""

    detail: str = Field(..., description="에러 메시지")
    error_code: str = Field(..., description="에러 코드")
