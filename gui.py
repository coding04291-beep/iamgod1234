import streamlit as st
import requests
import re
import pandas as pd
import time
from urllib.parse import unquote
import io

# --- 강력한 수집 함수 ---
def get_blog_posts(blog_id):
    posts = []
    page = 1
    
    # 실제 브라우저와 거의 동일한 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': f'https://blog.naver.com/PostList.naver?blogId={blog_id}',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    progress_bar = st.progress(0)
    
    while page <= 10:  # 일단 10페이지(약 300개) 수집
        # API 주소를 살짝 변경 (가장 최신 방식)
        url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={blog_id}&viewdate=&currentPage={page}&categoryNo=0&parentCategoryNo=0"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                st.error(f"네이버 접속 실패 (코드: {response.status_code})")
                break
                
            text = response.text
            
            # 정규표현식으로 제목, 날짜, 로그번호 추출
            titles = re.findall(r'"titleText":"([^"]+)"', text)
            dates = re.findall(r'"addDate":"([^"]+)"', text)
            log_nos = re.findall(r'"logNo":"([^"]+)"', text)
            
            if not titles:
                break
                
            for i in range(len(titles)):
                # 인코딩된 문자열 정화
                t = unquote(titles[i]).replace('\n', ' ').replace('\\', '').strip()
                posts.append({
                    '제목': t,
                    '날짜': dates[i] if i < len(dates) else '',
                    '링크': f"https://blog.naver.com/{blog_id}/{log_nos[i]}" if i < len(log_nos) else ''
                })
            
            page += 1
            progress_bar.progress(min(page / 10, 1.0))
            time.sleep(0.5) # 차단 방지를 위한 휴식
        except Exception as e:
            st.error(f"오류 발생: {e}")
            break
            
    return pd.DataFrame(posts).drop_duplicates()

# --- 웹 화면 구성 ---
st.set_page_config(page_title="네이버 블로그 추출기", page_icon="📝")
st.title("📝 네이버 블로그 글 목록 추출기")

blog_id_input = st.text_input("블로그 아이디를 입력하세요", "youngwookim77")

if st.button("🚀 수집 시작"):
    with st.spinner('네이버 서버에서 데이터를 가져오는 중입니다...'):
        df = get_blog_posts(blog_id_input)
        
    if not df.empty:
        st.success(f"총 {len(df)}개의 글을 수집했습니다!")
        st.write("### 📋 수집 데이터 미리보기 (상위 10개)")
        st.dataframe(df.head(10), use_container_width=True)
        
        # 엑셀 다운로드 버튼
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="💾 엑셀 파일(.xlsx) 받기",
            data=output.getvalue(),
            file_name=f"naver_blog_{blog_id_input}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("데이터를 찾을 수 없습니다. 아이디가 정확한지, 혹은 비공개 블로그인지 확인해 주세요.")
