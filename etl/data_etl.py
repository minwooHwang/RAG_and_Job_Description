#######
# 데이터 ETL 코드
#######
import pandas as pd
import json

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
        df[col] = df[col].map(lambda v: pd.NA if pd.isna(v) else (pd.NA if str(v).strip() == "" else str(v).strip()) ) # 삼항식과 람다함수를 이용함
        '''
        삼항식 설명
        [True] if [Condition] else [False]
        [참일때] if [조건문] else [거짓일때]
        '''
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

# 기술스택을 소문자로 바꾸고 리스트 형태로 바꿔주는 함수
def refined_tech_stack(df, source_col="tech_stack", target_col="tech_stack_list"):
    '''
    tech_stack 문자열을
    → 소문자
    → 리스트 형태로 변환
    '''
    series = df[source_col] # tech_stack 컬럼을 가져온다
    series = series.str.split(",") # 쉼표를 기준으로 나눈다 / .str -> 특정 컬럼을 문자열처럼 다룬다는 뜻 -> 리스트로 만들어주는 부분
    series = series.apply(
        lambda xs: [x.strip().lower() for x in xs] if isinstance(xs, list) else xs
    ) # 공백제거를 해주는 부분
    '''
    .apply는 .map()보다 더 광활한 범위에서 적용할 수 있다.
    map = “한 칸씩 같은 규칙으로 바꾸기” 전용
    apply = “한 칸(또는 한 줄)씩 함수 돌리기” 만능
    그 뒤에는 람다함수와 삼항조건(삼항식), 리스트 컴프리헨션이 적용된 코드다.
    람다 함수 xs는 isinstance(xs, list) -> xs가 리스트이면 / isinstance(비교대상, 조건) 비교대상이 조건과 같으면 참 아니면 거짓이다.
    xs 안에 있는 요소들을 하나씩 꺼내서 각 요소에 .strip() [== 공백제거 기능]을 적용한 결과를 새 리스트로 만든다.
    xs가 리스트가 아니라면 그냥 xs로 반환한다.
    '''
    df[target_col] = series

    return df


# 지역을 큰 틀에서 컬럼하나 더 만들어주는 함수(ex: 서울, 경기, 인천 등등)
def location_state(df, source_col="location", target_col="location_state"):
    '''
    location에서
    서울 / 경기 / 인천 등 광역 단위만 추출
    '''
    def extract_state(loc):
        if pd.isna(loc):
            return pd.NA
        
        if "서울" in loc:
            return "서울"
        elif "경기" in loc:
            return "경기"
        elif "대전" in loc:
            return "대전"
        elif "부산" in loc:
            return "부산"
        elif "광주" in loc:
            return "광주"
        else:
            return "기타"
    df[target_col] = df[source_col].apply(extract_state)

    return df

# 마감기한을 datatime 형식으로 바꿔주는 함수
def deadline_transform_to_datetime(df, source_col='deadline', target_col='deadline_dt'):
    '''
    마감기한 문자열을 datetime 형식으로 바꿔주는 함수
    '''
    df[target_col] = pd.to_datetime(
        df[source_col],
        errors="coerce"
    )
    '''
    pd.to_datetime(바꿀대상, errors="coerce")
    •	바꿀대상
    → 문자열, Series, 리스트 전부 가능
	•	errors="coerce"
    → 날짜로 못 바꾸면 NaT로 처리
    '''
    return df

# 리스트를 json 문자열로 바꿔서 저장해주는 함수 / csv파일은 리스트를 저장하면 그냥 문자열로 저장하기 때문에 json 문자열로 바꿔서 저장해야함.
def save_csv_with_json_lists(df, list_cols=("tech_stack_list",)):
    df_out = df.copy() # 원형 보존을 위함

    for col in list_cols:
        df_out[col] = df_out[col].apply(
            lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v
        )
    
    return df_out
    

def main():
    clean_df = normalize_missing_values(df, TEXT_COLUMNS)
    clean_df = remove_duplicates(clean_df, subset_col='url')
    clean_df = refined_tech_stack(clean_df, source_col="tech_stack", target_col="tech_stack_list")
    clean_df = location_state(clean_df, source_col="location", target_col="location_state")
    clean_df = deadline_transform_to_datetime(clean_df, source_col='deadline', target_col='deadline_dt')
    clean_df = save_csv_with_json_lists(clean_df, list_cols=("tech_stack_list",))
    clean_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()