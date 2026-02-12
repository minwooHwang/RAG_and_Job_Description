#######################
# PostgreSQL 연결코드
#######################
import psycopg2

def get_connection():
    conn = psycopg2.connect(
        dbname = "RAG_project",
        user = "hwangmin-u",
        password = "1234",
        host = "localhost",
        port = "5432"
    )

    return conn

def main():
    try:
        conn_db = get_connection()
        print("연결성공")
        conn_db.close()
    except Exception as e:
        print("연결 실패:", e)


if __name__ == "__main__":
    main()