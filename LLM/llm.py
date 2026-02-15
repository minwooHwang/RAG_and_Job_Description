###############################
# openai LLM 모델 불러오는 파일
'''
azure 서버에서 openai 모델을 불러올꺼다.
우선 .env파일에서 endpoint랑 key값 그리고 어떤 모델을 쓸지 정의해뒀으니
그걸 불러오고 if문을 통해서 테스트 코드를 집어넣자 불러와지는지 봐야하니까

그리고 나서 azure 서버에서 openai 모델을 불러보자
'''
###############################
import os
from dotenv import load_dotenv
from openai import OpenAI

# azure 서버에 접속 및 테스트
def get_azure_client() -> OpenAI: # 반환타입힌트를 통해서 OpenAI가 리턴될꺼라고 알려주기
    load_dotenv()

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        raise ValueError(".env에 AZURE_OPENAI_ENDPOINT 값 또는 AZURE_OPENAI_API_KEY가 입력되지 않았습니다.")

    return OpenAI(base_url=endpoint, api_key=api_key)

# LLM에게 대화를 거는 함수
def chat_bot(user_text: str) -> str:
    client = get_azure_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not deployment:
        raise ValueError(".env에 AZURE_OPENAI_DEPLOYMENT가 제대로 입력되지 않았습니다.")
    
    resp = client.chat.completions.create(
        model = deployment,
        messages=[
            {"role": "user", "content": user_text}
        ],
    )

    return resp.choices[0].message.content


def main():
    user_input = input("질문을 입력해주세요: ")
    ansewer = chat_bot(user_input)
    print("\n====== 답변입니다! ======")
    print(ansewer)

if __name__ == "__main__":
    main()