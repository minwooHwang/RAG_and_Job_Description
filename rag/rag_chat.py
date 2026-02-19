'''
1. 사용자의 질문 입력
2. 질문 임베딩
3. Top-k 50개 검색
4. LLM으로 filters JSON 추출
5. SQL 필터링
6. 최종 후보 3 ~ 5개 만들기
7. LLM 답변 생성 (근거문서 + 후보 공고 정보)
'''
# RAG 답변 생성
from llm.llm import chat_completion, question_embed
from rag.retriever import retrieve_top_k

# filters 추출
from rag.filters import extract_filters
from rag.sql_filter import filter_jobs

# RAG에서 문서를 검색하는 함수
def build_job_context(jobs) -> str:
    parts = []
    for i, j in enumerate(jobs, start=1):
        parts.append(
            f"[공고 {i}]\n"
            f"회사명: {j.get('company_name')}\n"
            f"공고명: {j.get('title')}\n"
            f"url: {j.get('url')}\n"
            f"지역: {j.get('location_state')}\n"
            f"경력: {j.get('work_experience')} (min={j.get('exp_min')}, max={j.get('exp_max')})\n"
            f"학력: {j.get('education')} (level={j.get('education_level')})\n"
            f"기술스택: {j.get('tech_stack')}\n"
            f"주요업무: {j.get('work')}\n"
            f"자격요건: {j.get('qualification')}\n"
            f"우대사항: {j.get('prefer')}\n"
            f"복지: {j.get('benefit')}\n"
            f"채용절차 및 기타 지원 유의사항: {j.get('process')}\n"
            f"유사도: {j.get('distance')}\n"
        )

    return "\n\n".join(parts)
    # 이를 통해 몇번 문서의 유사도가 얼마하고 임베딩 텍스는 뭔지 알 수 있다.
    # 줄바꿈을 2번 하는 이유는 단순한 줄바꿈이 아닌 문단을 나누기 위함이다.

def answer_with_Hybrid_rag(user_question: str, k_vec: int = 100, final_k: int =5) -> tuple[str, dict]:
    """
    k_vec: 벡터에서 넉넉하게 뽑는 top-k
    final_k: 최종 LLM에게 줄 후보 수
    return: (answer, debug_info)
    """
    # 질문 임베딩
    q_emb = question_embed(user_question) # 사용자의 질문을 받는 임베딩 함수 불러주고

    # 벡터 top-k 검색
    vec_docs = retrieve_top_k(q_emb, k = k_vec)
    vec_ids = {d["job_id"] for d in vec_docs} # -> retrieve_top_k의 결과에서 job_id만 뽑아서 집합으로 만들어준다.

    # distance 맵
    dist_map = {d["job_id"]: d["distance"] for d in vec_docs}

    # LLM -> filters JSON 추출
    filters = extract_filters(user_question)

    # SQL 필터링
    sql_jobs = filter_jobs(filters, limit=100)
    sql_ids = {j["id"] for j in sql_jobs}

    # 교집합으로 최종 후보 만들기. 없으면 SQL 결과로 대체
    final_ids = vec_ids & sql_ids # & 연산자는 집합의 교집합을 구하는 연산자이다. 즉, 벡터 검색과 SQL 필터링을 모두 통과한 공고의 ID만 남긴다.
    
    if len(final_ids) == 0:
        # fallback: SQL 결과만 사용
        final_jobs = sql_jobs[:final_k]
    else:
        final_jobs = [j for j in sql_jobs if j["id"] in final_ids]
        # distance 붙이고 정렬
        for j in final_jobs:
            j["distance"] = dist_map.get(j["id"])
        final_jobs = sorted(final_jobs, key=lambda x: x["distance"] or 999999)[:final_k]

    # context 만들기
    context = build_job_context(final_jobs)

    messages = [
        {
            "role": "system", 
            "content": (
                "너는 채용공고를 추천해주는 전문가다.\n"
                "반드시 제공된 문서 내용만 근거로 답한다.\n"
                "문서에 없는 정보는 추측하지 말고 '문서에 없음'이라고 답해라\n"
                "답변 간에는 반드시 url 형식으로 된 공고 링크를 포함시켜라.\n"
                "답변 간에는 반드시 기술스택, 지역, 경력, 학력 ,주요업무, 우대사항, 자격요건, 복지 및 혜택, 채용절차 및 기타 지원 유의사항 정보를 포함시켜라.\n"
            ),
        },
        {
            "role": "user", 
            "content": f"질문: {user_question}\n\n [참고 문서]: \n{context}",
        },
    ]
    answer = chat_completion(messages)

    debug_info = {
        "filters": filters,
        "vec_count": len(vec_docs),
        "sql_count": len(sql_jobs),
        "final_count": len(final_jobs),
        "used_fallback": len(final_ids) == 0,
    }

    return answer, debug_info

def main():
    print("Hybride RAG 기능을 통한 LLM 답변 서비스 시작 / exit를 입력하면 종료됩니다.")

    while True:
        user_question = input("\n 사용자 질문을 입력하세요: ").strip() # input() 함수를 사용하여 사용자로부터 질문을 입력받는다. strip()은 입력값의 양쪽 공백을 제거하는 함수이다.

        if user_question.lower() == "exit":
            print("Hybride RAG 기능을 통한 LLM 답변 서비스를 종료합니다.")
            break

        answer, debug_info = answer_with_Hybrid_rag(user_question, k_vec=50, final_k=5)
        print("\n============ 답변을 제공합니다 ============")
        print(answer)

        print("\n============ 디버그 정보 ============")
        print("filters:", debug_info["filters"])
        print("vec_count:", debug_info["vec_count"], "sql_count:", debug_info["sql_count"], "final_count:", debug_info["final_count"])
        print("---------------\n")
if __name__ == "__main__":
    main()