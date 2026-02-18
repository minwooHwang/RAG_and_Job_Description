###############################
# openai LLM 모델 불러오는 파일
'''
azure 서버에서 openai 모델을 불러올꺼다.
우선 .env파일에서 endpoint랑 key값 그리고 어떤 모델을 쓸지 정의해뒀으니
그걸 불러오고 if문을 통해서 테스트 코드를 집어넣자 불러와지는지 봐야하니까

그리고 나서 azure 서버에서 openai 모델을 불러보자
---------
llm.py는 rag_chat.py가 LLM을 사용할 수 있게 해주는 툴을 담은 파일이다.
-------
1. Azure OpenAl Clinent 연결
2. chat 모델 설정
3. embedding 모델 설정
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

# 대화에 사용할 LLM 모델을 고르는 함수
def chat_completion(messages, model: str | None = None) -> str:
    client = get_azure_client()
    deployment = model or os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        raise ValueError(".env에 사용할 LLM 모델을 누락하였습니다.")
    
    resp = client.chat.completions.create(
        model = deployment,
        messages = messages
    )
    
    return resp.choices[0].message.content

# 질문 임베딩에 사용할 모델을 고르는 함수
def question_embed(text: str, model: str | None = None ) -> list[float]:
    # | Noen = None의 의미는 model의 타입이 str일 수도 있고 None일 수도 있다는 것을 의미함.
    client = get_azure_client()
    deployment = model or os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
    if not deployment:
        raise ValueError(".env에 사용할 질문 임베딩 모델을 누락하였습니다.")
    
    resp = client.embeddings.create(
        model = deployment,
        input = text
    )

    return resp.data[0].embedding