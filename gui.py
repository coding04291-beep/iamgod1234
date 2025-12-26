import streamlit as st
import requests
import re
import pandas as pd
import time
from urllib.parse import unquote
import io

# --- 블로그 수집 함수 ---
def get_blog_posts(blog_id):
    posts = []
    page = 1
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    progress_bar = st.progress(0)
    status_text = st.empty()

    while page <= 20:  # 최대 20페이지까지 수집
        status_text.text(f"현재 {page}페이지 수집 중...")
        url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={blog_id}&viewdate=&currentPage={page}"
        
        try:
            response = requests.get(url, headers=headers)
            text = response.text
            
            titles = re.findall(r'"titleText":"([^"]+)"', text)
            dates = re.findall(r'"addDate":"([^"]+)"', text)
            log_nos = re.findall(r'"logNo":"([^"]+)"', text)
            
            if not titles: break
                
            for i in range(len(titles)):
                posts.append({
                    '제목': unquote(titles[i]).replace('\n', ' ').strip(),
                    '날짜': dates[i] if i < len(dates) else '',
                    '링크': f"https://blog.naver.com/{blog_id}/{log_nos[i]}" if i < len(log_nos) else ''
                })
            
            page += 1
            progress_bar.progress(page / 20)
            time.sleep(0.3)
        except:
            break
            
    return pd.DataFrame(posts).drop_duplicates()

# --- 웹 화면 구성 ---
st.set_page_config(page_title="네이버 블로그 수집기", layout="centered")
st.title("📝 네이버 블로그 글 목록 추출기")
st.write("블로그 아이디를 입력하면 글 목록을 엑셀로 만들어 드립니다.")

blog_url = st.text_input("블로그 주소 또는 아이디 입력", "youngwookim77")

if st.button("데이터 수집 시작"):
    # 주소에서 아이디만 추출하는 로직
    blog_id = blog_url.split('/')[-1] if '/' in blog_url else blog_url
    
    with st.spinner('데이터를 불러오는 중...'):
        df = get_blog_posts(blog_id)
        
    if not df.empty:
        st.success(f"총 {len(df)}개의 글을 찾았습니다!")
        st.dataframe(df.head(10))  # 미리보기
        
        # 엑셀 파일 변환 (메모리 상에서 처리)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📊 엑셀 파일 다운로드",
            data=output.getvalue(),
            file_name=f"blog_{blog_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("데이터를 가져오지 못했습니다. 아이디를 확인해주세요.")