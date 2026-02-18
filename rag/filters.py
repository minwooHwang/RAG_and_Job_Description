# LLM -> filters JSON 추출
# LLM이 사용자의 질문을 구조화하는 파일
import json
from llm.llm import chat_completion

def normalize_location_state(value: str | None):
    if not value:
        return None

    value = value.strip()

    mapping = {
        "경기도": "경기",
        "서울특별시": "서울",
        "인천광역시": "인천",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "대전광역시": "대전",
        "광주광역시": "광주",
    }

    return mapping.get(value, value)  # 매핑 없으면 그대로

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
        return {}
    
    filters["location_state"] = normalize_location_state(
        filters.get("location_state")
    )
    
    return filters