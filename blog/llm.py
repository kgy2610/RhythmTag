from environ import Env
from pathlib import Path
# from pyhub.llm import UpstageLLM
from pyhub.llm import OpenAILLM
import os

try:
    from pyhub.llm import UpstageLLM, OpenAILLM
    LLM_LIBRARY_AVAILABLE = True
except ImportError as e:
    print(f"pyhub.llm 라이브러리를 불러올 수 없습니다: {e}")
    LLM_LIBRARY_AVAILABLE = False
    UpstageLLM = None
    OpenAILLM = None

BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"

env = Env()
if ENV_PATH.exists():
    env.read_env(ENV_PATH, overwrite=True)
    print(f"✓ 환경변수 파일 로드: {ENV_PATH}")
else:
    print(f"✗ 환경변수 파일 없음: {ENV_PATH}")

OPENAI_API_KEY = env.str("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("✗ OPENAI_API_KEY가 설정되지 않았습니다.")
    llm = None
elif not LLM_LIBRARY_AVAILABLE:
    print("✗ LLM 라이브러리를 사용할 수 없습니다.")
    llm = None
else:
    try:
        # OpenAI LLM 사용
        llm = OpenAILLM(model="gpt-4o-mini")
        print("✓ OpenAI LLM 초기화 성공")
    except Exception as e:
        print(f"✗ LLM 초기화 실패: {e}")
        llm = None