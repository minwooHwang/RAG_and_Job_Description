#######
# 데이터 ETL 코드
#######
import pandas as pd

# 파일 경로 설정
INPUT_PATH = "data/jumpit_jobs.csv"
OUTPUT_PATH = "data/ETL_jumpit_jobs.csv"
df = pd.read_csv(INPUT_PATH)

# ETL 진행할 컬럼
TEXT_COLUMNS = [
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
    'location'
]

# 결측치 제거 함수
def normalize_missing_values(df, TEXT_COLUMNS):
    '''
    처음부터 빈 값이면 그대로 냅둠.
    문자열은 .strip()을 통해 빈 값이면 결측 처리함
    '''
    for col in TEXT_COLUMNS:
        df[col] = df[col].map(lambda v: pd.NA if pd.isna(v) else (pd.NA if str(v).strip() == "" else str(v).strip()) ) # 삼항식과 람다함수를 이용함 삼항식: 조건 if ~~(if가 참이면 조건 반환) else ~~
        # 처음부터 빈 값이면 그대로 냅두기
        # 문자열은 .strip()하기
        # strip 후 ""이면 결측 처리하기

    return df

# 중복제거 함수
def remove_duplicates(df, subset_col='url'):
    '''
    중복되는 값을 제거하는 함수
    subset_col을 기준으로 중복을 제거하고 전·후 row 수를 출력한 뒤 df 반환
    '''
    before = len(df)
    has_url = df[subset_col].notna() # .notna() -> 결측치면 False 반환 / .isna() -> 결측치면 True 반환

    df_url = df[has_url].drop_duplicates(subset=[subset_col], keep="first")
    '''
    .drop_duplicates -> 중복되는 행을 제거하는 판다스 함수
    df.drop_duplicates(subset=None, keep='first', inplace=False, ignore_index=False)
    - subset: 중복값을 검사할 열. 기본적으로 모든 열을 검사함
    - keep: 중복을 제거할 때 남길 행. first면 첫 값을 남기고 last면 마지막 값을 남김
    - inplace: 원본을 변경할지 선택
    - ignore_index: 원래 index를 무시할지 여부, True면 0,1,2, ..., n으로 부여됨
    '''
    df_no_url = df[~has_url] # ~has_url == has_url의 논리부정형
    
    df_out = pd.concat([df_url, df_no_url], ignore_index=True) #.concat()을 통해서 중복제거한 값과 나머지 값들을 합치는 과정을 거쳐야함.
    '''
    pandas에서 .concat()은 데이터프레임을 합치는 함수다.
    세로(행)끼리 결합
    pd.concat([df1, df2])
    가로(열)끼리 결합
    pd.concat([df1, df2, axis=1])
    '''

    after = len(df_out)
    print(f"중복제거 전: {before}, 중복제거 이후: {after}, 제거한 값: {before-after}")

    return df_out



def main():
    clean_df = normalize_missing_values(df, TEXT_COLUMNS)
    clean_df = remove_duplicates(clean_df, subset_col='url')
    clean_df.to_csv(OUTPUT_PATH, index = False, encoding= "utf-8-sig")

if __name__ == "__main__":
    main()