import streamlit as st
import pandas as pd
import re
from collections import Counter

from googleapiclient.discovery import build

from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="유튜브 댓글 심층 분석기",
    page_icon="🎬",
    layout="wide"
)

# ------------------------
# 디자인
# ------------------------

st.markdown("""
<style>

.stApp{
background:
linear-gradient(
135deg,
#0f172a,
#111827,
#1e293b
);
}

h1,h2,h3{
color:white;
}

</style>
""", unsafe_allow_html=True)

st.title("🎬 유튜브 댓글 심층 분석기")

st.write(
"""
유튜브 링크를 입력하면 댓글을 수집하여

- 댓글 통계
- 인기 댓글
- 자주 쓰인 단어
- 워드클라우드
- 댓글 분위기

를 분석합니다.
"""
)

# ------------------------
# 입력
# ------------------------

api_key = st.text_input(
    "🔑 YouTube API Key",
    type="password"
)

youtube_url = st.text_input(
    "📺 유튜브 링크"
)

# ------------------------
# 영상 ID 추출
# ------------------------

def extract_video_id(url):

    patterns = [
        r"v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

# ------------------------
# 댓글 수집
# ------------------------

def get_comments(api_key, video_id):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

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

        try:
    response = request.execute()

except Exception as e:
    st.error("API 호출 실패 😢")
    st.exception(e)
    st.stop()
        for item in response["items"]:

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "comment": snippet["textDisplay"],
                "likes": snippet["likeCount"]
            })

        next_page = response.get("nextPageToken")

        if not next_page:
            break

        if len(comments) >= 1000:
            break

    return pd.DataFrame(comments)

# ------------------------
# 분석
# ------------------------

if st.button("🚀 분석 시작"):

    if not api_key:
        st.error("API Key를 입력하세요.")
        st.stop()

    video_id = extract_video_id(youtube_url)

    if not video_id:
        st.error("올바른 유튜브 링크가 아닙니다.")
        st.stop()

    with st.spinner("댓글 수집 중..."):

        df = get_comments(
            api_key,
            video_id
        )

    if len(df) == 0:
        st.warning("댓글이 없습니다.")
        st.stop()

    st.success(f"댓글 {len(df)}개 수집 완료")

    # --------------------
    # 통계
    # --------------------

    col1,col2,col3 = st.columns(3)

    with col1:
        st.metric(
            "댓글 수",
            len(df)
        )

    with col2:
        st.metric(
            "총 좋아요",
            int(df["likes"].sum())
        )

    with col3:
        avg_len = df["comment"].str.len().mean()
        st.metric(
            "평균 댓글 길이",
            f"{avg_len:.1f}"
        )

    # --------------------
    # 인기 댓글
    # --------------------

    st.header("🔥 인기 댓글 TOP 10")

    top_comments = df.sort_values(
        "likes",
        ascending=False
    ).head(10)

    st.dataframe(
        top_comments,
        use_container_width=True
    )

    # --------------------
    # 단어 분석
    # --------------------

    text = " ".join(
        df["comment"].astype(str)
    )

    words = re.findall(
        r"[가-힣A-Za-z]{2,}",
        text
    )

    stopwords = {
        "합니다",
        "그리고",
        "진짜",
        "너무",
        "있는",
        "있는데",
        "영상",
        "정말",
        "ㅋㅋ",
        "ㅎㅎ"
    }

    words = [
        w for w in words
        if w not in stopwords
    ]

    counter = Counter(words)

    top_words = pd.DataFrame(
        counter.most_common(20),
        columns=["단어","빈도"]
    )

    st.header("📊 가장 많이 나온 단어")

    st.dataframe(
        top_words,
        use_container_width=True
    )

    # --------------------
    # 워드클라우드
    # --------------------

    st.header("☁️ 워드클라우드")

    try:

        wc = WordCloud(
            width=1200,
            height=600,
            background_color="white",
            font_path="NanumGothic.ttf"
        ).generate(" ".join(words))

    except:

        wc = WordCloud(
            width=1200,
            height=600,
            background_color="white"
        ).generate(" ".join(words))

    fig, ax = plt.subplots(
        figsize=(12,6)
    )

    ax.imshow(wc)
    ax.axis("off")

    st.pyplot(fig)

    # --------------------
    # 분위기 분석
    # --------------------

    positive_words = [
        "좋다",
        "최고",
        "감동",
        "재밌다",
        "사랑",
        "행복",
        "멋지다",
        "잘했다"
    ]

    negative_words = [
        "별로",
        "싫다",
        "최악",
        "실망",
        "짜증",
        "화난다",
        "아쉽다"
    ]

    positive = 0
    negative = 0

    for comment in df["comment"]:

        for p in positive_words:
            if p in comment:
                positive += 1

        for n in negative_words:
            if n in comment:
                negative += 1

    st.header("🧠 댓글 분위기")

    if positive > negative:

        st.success(
            "전반적으로 긍정적인 반응이 많습니다."
        )

    elif negative > positive:

        st.error(
            "전반적으로 부정적인 반응이 많습니다."
        )

    else:

        st.info(
            "긍정과 부정 반응이 비슷합니다."
        )

    # --------------------
    # 종합 분석
    # --------------------

    st.header("📋 종합 분석")

    top5 = ", ".join(
        top_words["단어"].head(5)
    )

    st.write(f"""
이 영상의 댓글은 총 **{len(df)}개** 분석되었습니다.

가장 많이 언급된 핵심 키워드는

**{top5}**

입니다.

좋아요가 많은 댓글을 기준으로 보면
시청자들의 관심은 해당 주제에 집중되어 있으며,
반복적으로 등장하는 단어가 주요 관심사를 보여줍니다.

워드클라우드를 통해
영상에 대한 시청자 인식을 시각적으로 확인할 수 있습니다.
""")
