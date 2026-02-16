# RAG and Job Description

Jumpit 채용공고를 크롤링하고, ETL/DB 적재/임베딩/RAG 질의응답까지 연결한 학습용 프로젝트입니다.

## 프로젝트 구조

```text
.
├─ crawler/         # 채용공고 크롤링 (Playwright)
├─ etl/             # CSV 정제
├─ db/              # PostgreSQL 연결/스키마/CSV 적재
├─ llm/             # Azure OpenAI 호출 유틸
├─ rag/             # 임베딩 적재 + 검색 + 챗
└─ data/            # 원본/정제 CSV
```

## 요구사항

- Python 3.10+
- PostgreSQL
- (권장) pgvector extension
- Azure OpenAI 계정/배포

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## 환경 변수 설정

`.env.sample`을 복사해 `.env`를 만들고 값 입력:

```bash
cp .env.sample .env
```

필수 키:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT` (채팅 모델)
- `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` (임베딩 모델)

## DB 준비

1. `db/connection.py`의 접속 정보(`dbname`, `user`, `password`, `host`, `port`)를 로컬 환경에 맞게 수정
2. `db/schema.sql` 실행해 `jumpit_jobs` 테이블 생성
3. `job_embeddings` 테이블도 생성 (예시)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS job_embeddings (
    job_id INT PRIMARY KEY REFERENCES jumpit_jobs(id) ON DELETE CASCADE,
    embedding vector(1536),
    embedding_text TEXT,
    model TEXT
);
```

참고: 임베딩 차원(1536)은 사용 모델에 맞춰 조정해야 합니다.

## 실행 순서

중요: 패키지 import를 위해 파일 직접 실행 대신 `python -m ...` 형태를 사용하세요.

```bash
# 1) 크롤링
python -m crawler.run

# 2) ETL
python -m etl.data_etl

# 3) CSV -> DB 적재
python -m db.load_csv

# 4) DB 데이터 임베딩 생성/적재
python -m rag.data_embedding

# 5) RAG 챗 실행
python -m rag.rag_chat
```

## 자주 발생하는 오류

- `ModuleNotFoundError: No module named 'db'`
  - 원인: `python path/to/file.py`로 직접 실행
  - 해결: 프로젝트 루트에서 `python -m db.load_csv`처럼 모듈 실행

- VS Code에서 다른 가상환경으로 실행됨
  - `.vscode/settings.json`에 아래 설정 권장
  - `"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"`
