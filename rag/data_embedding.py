'''
0. pgvector 테이블 만들기
1. PostgreSQL에서 데이터 가져오기
2. 하나의 공고를 문자열로 합치기
3. OpenAI Embedding API 호출하기
4. 벡터 생성
5. 생성한 벡터를 pgvector에 저장
'''
from db.connection import get_connection
from llm.llm import get_azure_client
from psycopg2.extras import RealDictCursor # psycopg2에 들어있는 딕셔너리 전용 커서 기능
import os
from openai import OpenAI

# PostgreSQL에서 데이터 가져오기
def get_data_db():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 딕셔너리로 받음으로써 컬럼명이 key가 되고 값은 value가 된다.
            cur.execute("""
                SELECT id, title, company_name, work, qualification, prefer, benefit
                FROM jumpit_jobs
            """)
            rows = cur.fetchall() #.fetchall() -> 쿼리 결과를 전부 다 가져오는 함수
            return rows
    except Exception as e:
        print("DB 연결, 조회에 실패하였습니다:", e)
        return []
    finally:
        conn.close()

# 문자열 합치는 함수
def build_embedding_text(row):
    parts = []

    if row['title']:
        parts.append(f"공고명: {row['title']}")
    if row['company_name']:
        parts.append(f"회사명: {row['company_name']}")
    if row['work']:
        parts.append(f"주요업무: {row['work']}")
    if row['qualification']:
        parts.append(f"지원조건: {row['qualification']}")
    if row['prefer']:
        parts.append(f"우대사항: {row['prefer']}")
    if row['benefit']:
        parts.append(f"복지: {row['benefit']}")
    
    return "\n".join(parts) # 하나의 문자열로 합치기 위해서 .join 사용

# 임베딩 API 호출
def embedding_model(text: str, client: OpenAI, deployment: str) -> list[float]:
    if not deployment:
        raise ValueError("임베딩 모델이 입력되지 않았습니다.")
    
    resp = client.embeddings.create(
        model = deployment,
        input = text
    )
    return resp.data[0].embedding

# 임베딩한 결과를 저장하는 함수
def save_embedding(job_id: int, embedding: list[float], text: str, model: str, conn) -> None:
    sql = """
        INSERT INTO job_embeddings (job_id, embedding, embedding_text, model)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (job_id)
        DO UPDATE SET
            embedding = EXCLUDED.embedding,
            embedding_text = EXCLUDED.embedding_text,
            model = EXCLUDED.model;
    """
    with conn.cursor() as cur:
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        cur.execute(sql, (job_id, embedding_str, text, model))

def main():
    print("데이터 임베딩 시작")
    client = get_azure_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
    rows = get_data_db()
    conn = get_connection()

    if not deployment: raise ValueError(".env에 임베딩 모델이 입력되지 않았습니다.")

    try:
        for idx, row in enumerate(rows, start=1):
            job_id = row['id']
            text = build_embedding_text(row)
            embedding = embedding_model(text, client, deployment)
            save_embedding(job_id, embedding, text, deployment, conn)
            if idx % 20 == 0:
                print(f"{idx} / {len(rows)} 처리 완료")
        conn.commit()
        print()
        print("임베딩 데이터 DB 적재 성공")
    except Exception as e:
        conn.rollback()
        print("임베딩 데이터 DB 적재 실패:", e)
    finally:
        conn.close()


if __name__ == "__main__":
    main()