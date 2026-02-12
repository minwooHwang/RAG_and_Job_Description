/*
테이블 구조(스키마) 정의
*/
-- 채용공고 테이블(ETL_jumpit_jobs.csv)

DROP TABLE IF EXISTS jumpit_jobs;
CREATE TABLE jumpit_jobs(
    id SERIAL PRIMARY KEY,
    url TEXT,
    title TEXT,
    company_name TEXT,
    tech_stack JSONB,
    work TEXT,
    qualification TEXT,
    prefer TEXT,
    benefit TEXT,
    process TEXT,
    work_experience TEXT,
    education TEXT,
    deadline DATE,
    location TEXT,
    location_state TEXT
)
