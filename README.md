# Jumpit RAG Job Recommender

Jumpit 채용공고를 수집하고, 정제/적재/임베딩/검색/생성까지 한 번에 연결한 Hybrid RAG 프로젝트입니다.  
사용자 질문을 구조화된 필터로 바꾼 뒤(SQL), 벡터 검색 결과(pgvector)와 결합해 최종 추천 답변을 생성합니다.

## 1. Project Summary

- 데이터 수집: Playwright 기반 크롤러로 채용공고 수집
- 데이터 가공: ETL 파이프라인으로 결측/중복/스택/지역/경력/학력 컬럼 정규화
- 데이터 저장: PostgreSQL + JSONB + pgvector
- 검색 전략: Vector Search + SQL Filter를 결합한 Hybrid RAG
- 생성 모델: Azure OpenAI(Chat/Embedding)

## 2. Architecture

```text
[crawler/run.py]
   -> data/jumpit_jobs.csv

[etl/data_etl.py]
   -> data/ETL_jumpit_jobs.csv

[db/load_csv.py]
   -> jumpit_jobs (PostgreSQL)

[rag/data_embedding.py]
   -> job_embeddings (pgvector)

[rag/rag_chat.py]
   -> (1) question embedding
   -> (2) vector top-k (rag/retriever.py)
   -> (3) LLM filter extraction (rag/filters.py)
   -> (4) SQL filter query (rag/sql_filter.py)
   -> (5) intersection/fallback + answer generation
```

## 3. Tech Stack

- Language: Python 3.12
- Crawling: Playwright
- Data: pandas
- DB: PostgreSQL, psycopg2, JSONB, pgvector
- LLM: Azure OpenAI API (`openai` SDK)
- Env: python-dotenv

## 4. Directory Guide

```text
.
├─ crawler/
│  └─ run.py               # Jumpit 공고 크롤링 -> CSV 저장
├─ etl/
│  └─ data_etl.py          # 데이터 정제/파생 컬럼 생성
├─ db/
│  ├─ schema.sql           # jumpit_jobs 기본 스키마
│  ├─ connection.py        # PostgreSQL 연결 유틸
│  └─ load_csv.py          # CSV -> DB UPSERT
├─ llm/
│  └─ llm.py               # Azure OpenAI client/chat/embed 유틸
├─ rag/
│  ├─ data_embedding.py    # 공고 임베딩 생성/적재
│  ├─ retriever.py         # vector top-k 검색
│  ├─ filters.py           # 질문 -> JSON filters 추출/정규화
│  ├─ sql_filter.py        # filters -> SQL where 구성/실행
│  └─ rag_chat.py          # Hybrid RAG 답변 생성
└─ requirements.txt
```

## 5. Setup

### 5.1 Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### 5.2 Environment Variables

`.env.sample` 복사 후 `.env` 작성:

```bash
cp .env.sample .env
```

필수 값:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT` (chat model)
- `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` (embedding model)

### 5.3 Database

1. `db/connection.py` 접속 정보 수정
2. `db/schema.sql` 실행
3. `job_embeddings` 테이블 생성
4. `jumpit_jobs.url` unique 제약 추가 (UPSERT 충돌 기준)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS job_embeddings (
    job_id INT PRIMARY KEY REFERENCES jumpit_jobs(id) ON DELETE CASCADE,
    embedding vector(1536),
    embedding_text TEXT,
    model TEXT
);

ALTER TABLE jumpit_jobs
ADD CONSTRAINT jumpit_jobs_url_key UNIQUE (url);
```

참고: 임베딩 차원(`1536`)은 모델 차원과 일치해야 합니다.

## 6. Run Pipeline

중요: 패키지 import 문제를 피하려면 파일 직접 실행 대신 `python -m ...`를 사용합니다.

```bash
# 1) Crawl
python -m crawler.run

# 2) ETL
python -m etl.data_etl

# 3) CSV -> PostgreSQL (UPSERT)
python -m db.load_csv

# 4) Embedding -> pgvector
python -m rag.data_embedding

# 5) Hybrid RAG Chat
python -m rag.rag_chat
```

## 7. Key Implementation Points

- `db/load_csv.py`
  - `ON CONFLICT (url) DO UPDATE` 기반 UPSERT
  - 재실행 시 중복 적재를 방지하고 기존 행을 최신 CSV 값으로 갱신
- `rag/data_embedding.py`
  - `job_id` 기준 업서트로 임베딩 동기화
- `rag/rag_chat.py`
  - Vector top-k + SQL 필터 교집합 기반 후보 생성
  - 교집합이 비면 SQL 결과 fallback
- `rag/filters.py`
  - 질문의 지역 표현(예: 서울시/서울특별시)을 canonical state로 정규화

## 8. Troubleshooting

- `ModuleNotFoundError: No module named 'db'`
  - 원인: `python path/to/file.py` 직접 실행
  - 해결: 프로젝트 루트에서 `python -m db.load_csv`처럼 실행

- `there is no unique or exclusion constraint matching the ON CONFLICT specification`
  - 원인: `ON CONFLICT (url)` 대상 unique 제약 없음
  - 해결: `jumpit_jobs.url`에 `UNIQUE` 제약 추가

- `integer out of range` during CSV load
  - 원인: 결측치 `NaN`가 정수 컬럼에 캐스팅되는 경우
  - 해결: `df.astype(object).where(pd.notna(df), None)`로 `None` 처리 후 insert

- VS Code에서 다른 venv가 선택되는 문제
  - 권장 설정: `.vscode/settings.json`
  - `"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"`

## 9. Resume-Friendly Highlights

- 크롤링부터 검색/생성까지 이어지는 End-to-End 데이터/LLM 파이프라인 설계 및 구현
- PostgreSQL `UPSERT`와 `UNIQUE` 제약으로 데이터 중복/동기화 문제 해결
- Hybrid RAG(Vector + SQL) 구조로 검색 정확도와 제어 가능성 개선
- 자연어 질문을 구조화 조건(JSON)으로 변환해 실서비스형 질의 인터페이스 구현
