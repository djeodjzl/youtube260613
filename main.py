import streamlit as st
import pandas as pd
import re
from collections import Counter

from googleapiclient.discovery import build
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# -------------------------
# 설정
# -------------------------
st.set_page_config(
    page_title="🎬 유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("🎬 유튜브 댓글 심층 분석기")

st.markdown("""
유튜브 링크와 API Key를 입력하면 댓글을 분석합니다.

✔ 댓글 수집  
✔ 인기 댓글  
✔ 단어 분석  
✔ 워드클라우드  
✔ 감정 분석  
""")

# -------------------------
# 입력
# -------------------------
api_key = st.text_input("🔑 YouTube API Key", type="password")
url = st.text_input("📺 YouTube URL")

# -------------------------
# 영상 ID 추출
# -------------------------
def extract_video_id(url):
    patterns = [
        r"v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None

# -------------------------
# 댓글 수집
# -------------------------
def get_comments(api_key, video_id):

    youtube = build("youtube", "v3", developerKey=api_key)

    comments = []
    next_page = None

    while True:

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page,
            textFormat="plainText"
        )

        # 🔥 안정 처리 (여기가 핵심)
        try:
            response = request.execute()

        except Exception as e:
            st.error("API 호출 실패 😢")
            st.exception(e)
            return pd.DataFrame()

        for item in response.get("items", []):
            sn = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "comment": sn["textDisplay"],
                "likes": sn["likeCount"]
            })

        next_page = response.get("nextPageToken")

        if not next_page:
            break

        if len(comments) > 1000:
            break

    return pd.DataFrame(comments)

# -------------------------
# 실행
# -------------------------
if st.button("🚀 분석 시작"):

    if not api_key or not url:
        st.warning("API Key와 URL을 입력하세요")
        st.stop()

    video_id = extract_video_id(url)

    if not video_id:
        st.error("유효하지 않은 유튜브 URL입니다.")
        st.stop()

    with st.spinner("댓글 수집 중..."):
        df = get_comments(api_key, video_id)

    if df.empty:
        st.warning("댓글을 가져오지 못했습니다.")
        st.stop()

    st.success(f"댓글 {len(df)}개 수집 완료")

    # -------------------------
    # 통계
    # -------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("댓글 수", len(df))

    with col2:
        st.metric("총 좋아요", int(df["likes"].sum()))

    with col3:
        st.metric("평균 길이", round(df["comment"].str.len().mean(), 1))

    # -------------------------
    # 인기 댓글
    # -------------------------
    st.subheader("🔥 인기 댓글 TOP 10")
    st.dataframe(df.sort_values("likes", ascending=False).head(10))

    # -------------------------
    # 단어 분석
    # -------------------------
    text = " ".join(df["comment"].astype(str))

    words = re.findall(r"[가-힣A-Za-z]{2,}", text)

    stopwords = {
        "영상","진짜","너무","ㅋㅋ","ㅎㅎ","그리고","정말","합니다"
    }

    words = [w for w in words if w not in stopwords]

    counter = Counter(words)

    top_words = pd.DataFrame(counter.most_common(20),
                             columns=["단어", "빈도"])

    st.subheader("📊 단어 빈도")
    st.dataframe(top_words)

    # -------------------------
    # 워드클라우드
    # -------------------------
    st.subheader("☁️ 워드클라우드")

    try:
        wc = WordCloud(
            width=1000,
            height=500,
            background_color="white",
            font_path="NanumGothic.ttf"  # 있으면 사용
        ).generate(" ".join(words))

    except:
        wc = WordCloud(
            width=1000,
            height=500,
            background_color="white"
        ).generate(" ".join(words))

    fig, ax = plt.subplots()
    ax.imshow(wc)
    ax.axis("off")
    st.pyplot(fig)

    # -------------------------
    # 감정 분석 (간단 버전)
    # -------------------------
    positive = ["좋다", "최고", "재밌", "감동", "사랑"]
    negative = ["별로", "싫", "최악", "짜증", "실망"]

    pos = sum(any(p in c for p in positive) for c in df["comment"])
    neg = sum(any(n in c for n in negative) for c in df["comment"])

    st.subheader("🧠 감정 분석")

    if pos > neg:
        st.success("👍 긍정적인 반응이 많습니다")
    elif neg > pos:
        st.error("👎 부정적인 반응이 많습니다")
    else:
        st.info("⚖️ 반응이 비슷합니다")
