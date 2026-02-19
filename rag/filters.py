# LLM -> filters JSON 추출
# LLM이 사용자의 질문을 구조화하는 파일
import json
from llm.llm import chat_completion
import re

# ETL에서 만든 location_state값
VALID_STATES = {"서울", "경기", "인천", "부산", "대구", "대전", "광주", "포항", "기타"}

# 질문 & LLM 출력에서 올 수 있는 다양한 지역 표현들을 location_state의 값으로 통일
STATE_VARIANTS = {
    "서울": ["서울", "서울시", "서울특별시"],
    "경기": ["경기", "경기도"],
    "대전": ["대전", "대전시", "대전광역시"],
    "부산": ["부산", "부산시", "부산광역시"],
    "광주": ["광주", "광주시", "광주광역시"],
    "인천": ["인천", "인천시", "인천광역시"],
    "대구": ["대구", "대구시", "대구광역시"],
    "포항": ["포항", "포항시"],
    "기타": ["기타"]
}

def normalize_location_state(value: str | None, question: str | None = None) -> str | None:
    # 질문에 대해서 룰 베이스를 먼저 잡기
    '''
    re.sub() -> 정규표현식으로 문자열을 치환하는 함수
    re.sub(패턴, 바꿀문자열, 원본문자열)
    q = re.sub(r"\s+", "", question) => \s+(공백/탭/줄바꿈 등 연속 공백)을 ""(빈 문자열)로 바꿔서 질문 문자열의 공백을 전부 제거한다.
    ex). 서울시 강남 구 -> 서울시강남구
    '''
    if question:
        q = re.sub(r"\s+", "", question) # 질문에서 공백 제거
        for canonical, variants in STATE_VARIANTS.items():
            '''
            .items() -> 딕셔너리에서 키와 값을 동시에 가져오는 함수 / 키와 값을 같이 순회할때 사용한다.
            d = {"a": 1, "b": 2}
            for k, v in d.items():
                print(k, v)
                -> a 1
                -> b 2
            '''
            if any(v in q for v in variants):
                '''
                any() -> 반복 가능한 객체에서 하나라도 참이 있으면 참을 반환하는 함수
                any(반복가능객체) -> any(v in q for v in variants) -> variants 리스트에서 v를 하나씩 꺼내서 q에 있는지 확인해서 하나라도 있으면 True 반환
                v in q for v in variants -> 제너레이터 표현식임
                (식 for 변수 in 반복가능객체 if 조건)
                '''
                return canonical
    
    # LLM이 준 값을 정규화하기
    if not value:
        return None
    # 여기서 Value는 LLM이 JSON으로 뽑은 location_state임. 따라서 value는 사용자의 질문에서 추출된 location_state값이거나 None일 수 있다.
    # LLM이 지역을 못 뽑았으면 그냥 None을 반환한다는 뜻임.
    
    v = value.strip()

    # 제대로 답변하면 그대로
    if v in VALID_STATES:
        return v
    
    vv = re.sub(r"\s+", "", v)
    '''
    LLM이 location_state 값을 뽑긴 했는데 이상하게 뽑았을 때도 룰 베이스로 정규화 시도하기
    예를 들어 "서울 시"라고 뽑았을 때 "서울시"로 바꿔주는 식으로, 부산 광역시라고 뽑으면 부산광역시로
    '''
    for canonical, variants in STATE_VARIANTS.items():
        if any(x.replace(" ", "") in vv for x in variants):
            '''
            문자열.replace(기존값, 새값, count) -> 기존값을 새값으로 바꿔주는 함수
            x.replace(" ", "") -> 각 지역 표현에서 공백을 제거
            str.replace(old, new, count)
            count 생략: 전부 바꿈
            count=1 : 앞에서 1개만 바꿈
            count=n : 앞에서 n개만 바꿈
            '''
            return canonical
        
    return None

def extract_filters(question: str) -> dict:
    # 사용자의 질문을 json으로 바꿔주는 함수
    prompt = f"""
    사용자의 질문에서 채용 조건을 JSON으로 추출할 것.
    반드시 아래 형식으로만 출력할 것.
    {{
        "location_state": string or null,
        "education_level": int or null,
        "tech_stack": list or strings,
        "company_name": string or null,
        "exp_min": int or null,
        "exp_max": int or null
    }}

    질문: {question}
    """

    messages = [
        {"role": "system", "content": "너는 채용 조건을 구조화하는 전문가다. JSON만 출력하라."},
        {"role": "user", "content": prompt}
    ]

    response = chat_completion(messages)

    try:
        filters = json.loads(response)
        # json.loads() -> JSON 문자열을 파이썬 객체로 변환하는 함수
        # '{"a":1}' -> {"a": 1} (dict)
        # '[1,2,3]' -> [1, 2, 3] (list)
    except Exception:
        filters = {}
    
    filters["location_state"] = normalize_location_state(
        filters.get("location_state"),
        question=question
    )

    return filters