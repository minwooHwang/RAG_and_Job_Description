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

# RAG에서 문서를 검색하는 함수
def build_context(docs) -> str:
    parts = []
    for i, d in enumerate(docs, start=1):
        parts.append(f"[문서 {i}] (distance={d['distance']})\n{d['embedding_text']}")
        # 이를 통해 몇번 문서의 유사도가 얼마하고 임베딩 텍스는 뭔지 알 수 있다.

    return "\n\n".join(parts) # 줄바꿈을 2번 하는 이유는 단순한 줄바꿈이 아닌 문단을 나누기 위함이다.

def answer_with_rag(user_question: str, k: int = 5) -> tuple[str, str]:
    q_emb = question_embed(user_question) # 사용자의 질문을 받는 임베딩 함수 불러주고
    docs = retrieve_top_k(q_emb, k=k) # 문서에 대해서 top_k를 뽑아주는 함수 불러주고
    context = build_context(docs)

    messages = [
        {"role": "system", "content": "너는 채용공고를 추천해주는 전문가야. 답변은 제공된 문서를 근거로만 답해"},
        {"role": "user", "content": f"질문: {user_question}\n\n 참고 문서: \n{context}"}
    ]
    answer = chat_completion(messages)

    return answer, context

def main():
    print("RAG 기능을 통한 LLM 답변 서비스 시작 / exit를 입력하면 종료됩니다.")

    while True:
        user_question = input("\n 사용자 질문을 입력하세요: ")

        if user_question.lower() == "exit":
            print("RAG 기능을 통한 LLM 답변 서비스를 종료합니다.")
            break

        answer, context = answer_with_rag(user_question)
        print("\n============ 답변을 제공합니다 ============")
        print(answer)
        '''
        print("\n===== 참고 문서 (RAG Context) =====")
        print(context)
        print("=================================\n")
        '''
    
if __name__ == "__main__":
    main()