# JSON -> SQL 생성 및 실행
# filters.py에서 구조화된 조건을 DB에 실제로 적용하는 단계
import json
from db.connection import get_connection
from psycopg2.extras import RealDictConnection

def filter_jobs(filters: dict, limit: int=10):
    conn = get_connection()
    where_clauses = []
    values = []

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
    if filters.get("commpanny_name"):
        where_clauses.append("company_name ILIKE %s")
        values.append(f"%{filters['company_name']}%")
    
    # exp_min / exp_max
    if filters.get("exp_min") is not None:
        where_clauses.append("exp_min >= %s")
        values.append(filters["exp_min"])
    
    if filters.get("exp_max") is not None:
        where_clauses.append("(exp_max <= %s OR exp_max IS NULL)")
        values.append(filters["exp_max"])
    
    # tech_stack
    techs = filters.get("tech_stack") or []
    if isinstance(techs, str):
        techs = [techs]
        # isinstance(값, 타입) -> 객체가 특정 타입인지 확인하는 함수
        # isinstance(obj, type)
        # isinstance(3, int) -> True 출력
    
    for t in techs:
        where_clauses.append("tech_stack @> %s::jsonb")
        values.append(json.dumps([t.lower()], ensure_ascii=False))

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    sql = f"""
        SELECT *
        FROM jumpit_jobs
        {where_sql}
        LIMIT %s;
    """
    values.append(limit)

    try:
        with conn.cursor(cursor_factory=RealDictConnection) as cur:
            cur.execute(sql, values)
            return cur.fetchall()
    finally:
        conn.close()
