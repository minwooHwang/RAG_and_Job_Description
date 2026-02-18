# JSON -> SQL 생성 및 실행
# filters.py에서 구조화된 조건을 DB에 실제로 적용하는 단계
import json
from db.connection import get_connection
from psycopg2.extras import RealDictCursor

def filter_jobs(filters: dict, limit: int=10):
    conn = get_connection()
    where_clauses = []
    # SQL의 조건문 조각(문자열)을 모아두는 리스트 / SQL 문장 뼈대
    values = []
    # %s 자리에 실제로 들어갈 값들을 모아두는 리스트 / SQL 문장 뼈대에 끼워 넣을 값

    # location_state
    if filters.get("location_state"):
        # dict.get() -> 딕셔너리에서 키 값을 꺼내는 함수
        # d.get(key, default)
        # 키가 있으면 해당 값 반환
        # 키가 없으면 default 반환, 안 쓰면 기본 None 반환
        where_clauses.append("location_state = %s")
        values.append(filters["location_state"])#
    
    # education_level
    if filters.get("education_level") is not None:
        where_clauses.append("education_level >=%s")
        values.append(filters["education_level"])
    
    # companny_name
    if filters.get("companny_name"):
        where_clauses.append("company_name ILIKE %s")
        values.append(f"%{filters['company_name']}%")
    
    # exp_min / exp_max
    if filters.get("exp_min") is not None:
        where_clauses.append("exp_min >= %s")
        values.append(filters["exp_min"])
    
    if filters.get("exp_max") is not None:
        where_clauses.append("(exp_max <= %s OR exp_max IS NULL)")
        '''
        최대 경력이 사용자가 원하는 최대값 이하인 공고만 고르자
        exp_max가 NULL인 공고도 포함시킴
        NULL을 포함시키는 이유는 3년 이하의 경력을 찾을때 경력무관도 지원 가능 대상에 포함이기 떄문.
        append()는 조건 문장을 리스트에 추가한다는 뜻임
        NULL로 처리한다는게 아니라 DB에 NULL인 행도 통과시키겠다는 뜻임
        '''
        values.append(filters["exp_max"])
    
    # tech_stack
    techs = filters.get("tech_stack") or []
    '''
    tech_stack이 없으면 None이니까 []로 바꿔버린다
    즉, 기술스택 조건이 없으면 for문이 돌지 않게 해준다.
    '''
    if isinstance(techs, str):
        techs = [techs]
        '''
        isinstance(값, 타입) -> 객체가 특정 타입인지 확인하는 함수
        isinstance(obj, type)
        isinstance(3, int) -> True 출력
        techs가 문자열이면 리스트로 감싸겠다는 의미
        for문은 리스트로 돌리는게 편하므로 문자열이면 ["문자열"]으로 통일해버림.
        '''
    
    for t in techs:
        where_clauses.append("tech_stack @> %s::jsonb")
        values.append(json.dumps([t.lower()], ensure_ascii=False))
    '''
    위에 코드들은 전부 AND 방식(전부 포함)이다. 따라서 기술이 여러 개면 조건도 여러 개가 필요하므로 for문이 필요하다
    json.dumps() -> 파이썬의 리스트를 JSON의 문자열로 바꿔주는 함수. ex). ["python"] -> JSON의 문자열로 바꿔줌
    ensure_ascii=False -> 한글 같은 유니코드 문자를 바꾸지말고 그대로 두라는 의미임.
    json.dumps(["머신러닝"], ensure_ascii=False)
    -> '["머신러닝"]'

    json.dumps(["머신러닝"], ensure_ascii=True)
    -> '["\\uba38\\uc2e0\\ub7ec\\ub2dd"]'
    '''

    '''
    조건이 하나도 없으면 WHERE를 만들면 안됨
    조건이 있으면 WHERE + 조건들을 AND로 묶어야함.
    근데 우리는 지금 조건이 몇개 걸릴지 모름(회사지역, 경력, 학력 등등)
    '''
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
        '''
        위 코드가 해당하는 것들을 SQL 문장으로 만들어준다.
        .join() -> 문자열들을 구분자로 이어붙이는 문자열 함수다
        "구분자".join(문자열_반복가능객체)
        ", ".join(["a", "b", "c"]) -> "a, b, c"
        '''
    
    sql = f"""
        SELECT *
        FROM jumpit_jobs
        {where_sql}
        LIMIT %s;
    """

    values.append(limit)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # cursor_factory -> 커서 동작 방식/ 반환 형태를 지정하는 옵숀
            # RealDictCursor: psycopg2의 커서 클래스이고 조회 결과를 튜플이 아닌 dict 형태로 반환함
            cur.execute(sql, values)
            return cur.fetchall()
    finally:
        conn.close()
