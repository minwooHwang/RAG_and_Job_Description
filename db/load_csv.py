#######################
# ETL 끝난 CSV -> DB insert
#######################
from db.connection import get_connection
import pandas as pd

CSV_PATH = "data/ETL_jumpit_jobs.csv"
TABLE_NAME = "jumpit_jobs"

COLUMNS = [
    'url',
    'title',
    'company_name',
    'tech_stack',
    'work',
    'qualification',
    'prefer',
    'benefit',
    'process',
    'work_experience',
    'education',
    'deadline',
    'location',
    'location_state' 
]

def main():
    df = pd.read_csv(CSV_PATH)

    df = df.where(pd.notna(df), None)
    '''
    비어있는 값 체크: isna()
    값이 있는지 체크: notna()
    df.where(cond, other=...) -> 조건을 만족하면 원래 값 유지, 조건을 만족하지 않으면 other로 바꾸는 함수
    '''
    # INSERT SQL 문자열 만들기
    cols_sql = ", ".join(COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    sql = f"INSERT INTO {TABLE_NAME} ({cols_sql}) VALUES ({placeholders});" # SQL 쿼리 실행문

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # .cursor() -> DB에 연결해서 이제 뭔갈 하겠다는 의미
            # 즉, DB 연결 객쳬(conn)에서 쿼리를 실행할 작업용 객체(cursor)를 만드는 함수다
            # 여기에 뭘 써야한다는거지?
            # TODO 2) df를 순회하면서 한 row씩 insert
            # 힌트:
            # for _, row in df.iterrows():
            #     values = [row[c] for c in COLUMNS]
            #     cur.execute(sql, values)
            # df.iterrows() -> (index, row) 두 개짜리 튜플을 한 줄씩 반환해준다(행, 열을 줌) / 각 행을 반복할 수 있게 해주는 함수임.
            # 각 행을 순차적으로 처리할 때 유용함. 각 행에 대해 행의 인덱스와 데이터를 반환해준다.
            # for문에서 _를 쓰는건 값을 받아오기는 하지만 실제로는 사용하지 않는다를 의미한다.
            # 즉, 해당값은 사용하지 않겠다는 것을 의미하는 관례적 변수명이다.
            for _, row in df.iterrows():
                values = [row[i] for i in COLUMNS]
                cur.execute(sql, values)
                # .execute() 함수는 커서(cur)가 SQL문을 DB에 실행할 때 쓰는 메서드다.
                # cur.execute(sql, params) 형태를 띄고 있다. / params -> SQL 안의 자리표시자(placeholders)에 넣을 실제 값을 의미함.
        conn.commit()
        print("적재 완료")
    except Exception as e:
        conn.rollback()
        print("적재 실패:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()