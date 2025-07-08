from blog.llm import llm

def music_post_create(artist, song_title, youtube_link):
    # 가수, 노래 제목, 유튜브 링크를 받아 음악 추천 블로그를 작성
    prompt = f"""
        다음 정보를 바탕으로 음악 추천 블로그 포스트를 작성해주세요 :

        - 가수: {artist}
        - 노래 제목: {song_title}
        - 유튜브 링크: {youtube_link}

        블로그 포스트는 다음과 같은 구조로 작성해주세요 :
        1. 매력적인 소제목
        2. 노래 소개(가수와 곡에 대한 간단하고 매력적인 설명)
        3. 이 노래의 특징과 매력 포인트 (멜로디, 가사, 분위기 등)
        4. 가사를 인용한 노래 소개 2가지
        5. 추천 이유(이 노래를 듣기 좋은 상황이나 분위기)
        6. 추천하고자 하는 대상
        7. 아래에 작성할, 사용자가 참고 가능한 해당 글 관련 #태그 5개 정도를 추천해주세요.

        요구사항 :
        - 모든 글은 존댓말로 작성
        - 친근하고 경험과 감정을 담아서 작성
        - 읽는 사람이 공감할 수 있는 내용으로 작성
        - 적절한 이모티콘을 사용하여 생동감 있게 작성
        - 각 문단은 3~4문장으로 구성
        - 맞춤법 및 띄어쓰기 검수 후 작성
        - 제목은 예시를 참고하여 작성해주세요.
            예시1) 가수 명: Mrs. GREEN APPLE, 노래 제목: ‘愛情と矛先’(애정과 창끝), 유튜브 링크: https://www.youtube.com/watch?v=_kW0MkNW1Ko&pp=ygU0bXJzLmdyZWVuIGFwcGxlIC0g5oSb5oOF44Go55-b5YWIICjslaDsoJXqs7wg7LC964GdKdIHCQnBCQGHKiGM7w%3D%3D
                    맑은 선율에 담긴 내면의 무기 – Mrs. GREEN APPLE ‘愛情と矛先’(애정과 창끝)
            예시2) 가수 명: 기리보이, 재키와이 노래 제목: 호랑이소굴, 유튜브 링크: https://www.youtube.com/watch?v=XyuQREKKgM0&pp=ygUS7Zi4656R7J207IaM6rW0IG120gcJCcEJAYcqIYzv
                    “호랑이 소굴, 그 안의 우리” – 기리보이 × 재키와이 ‘호랑이소굴 (Feat. Jvcki Wai)’

        블로그는 한국어로 작성해주세요.
        가사에 영어 또는 일본어 등 한국어가 아닌 언어가 있을 경우,
        원어로 작성한 후 줄바꿈을 하여 해당 가사의 해석을 한국어로 표기해주세요.
        """
    
    try:
        # llm 모듈 임포트 확인
        from .llm import llm
        
        # 스트리밍 방식으로 응답 생성
        blog_content = ""
        for chunk in llm.ask(prompt, stream=True):
            if hasattr(chunk, 'text'):
                blog_content += chunk.text
            else:
                blog_content += str(chunk)
        
        # 최소 길이 확인
        if len(blog_content.strip()) < 50:
            raise ValueError("생성된 내용이 너무 짧습니다.")
        
        return blog_content.strip()
        
    except ImportError as e:
        raise ImportError(f"LLM 모듈을 불러올 수 없습니다: {e}")
    except Exception as e:
        raise Exception(f"블로그 생성 중 오류가 발생했습니다: {str(e)}")