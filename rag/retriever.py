# top-k 검색
from db.connection import get_connection
from psycopg2.extras import RealDictCursor # psycopg2에 들어있는 딕셔너리 전용 커서 기능

def retrieve_top_k(query_embedding: list[float], k: int = 5 ):
    # 쿼리 임베딩은 리스트형식이고 안에 값은 소수점 포함, top_k는 5까지 뽑는다.
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    sql = """
        SELECT
            job_id,
            embedding_text,
            (embedding <=> %s::vector) AS distance
        FROM job_embeddings
        ORDER BY distance ASC
        LIMIT %s;
    """
    # 코사인 유사도로 비교함. 

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory = RealDictCursor) as cur:
            cur.execute(sql, (embedding_str, k))
            return cur.fetchall()
            '''
            .fetchall() -> 직전에 실행한 SELECT 결과를 전부 가져오는 함수임.
            '''
    finally:
        conn.close()