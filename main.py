# main.py
import os
import pandas as pd
import streamlit as st
import tempfile
from shutil import move
from datetime import datetime

# ──────────────────────────────
# Page & Cute Styling (풍선 제거)
# ──────────────────────────────
st.set_page_config(page_title="출석체크 (1부/2부)", layout="wide", page_icon="🧸")

# 귀여운 배너/칩/카드 스타일
st.markdown("""
<style>
:root {
  --chip-green-bg:#E6FCEB; --chip-green-fg:#166534; --chip-green-bd:#92F2A8;
  --chip-gray-bg:#F3F4F6; --chip-gray-fg:#374151; --chip-gray-bd:#E5E7EB;
  --card-bg: var(--secondary-background-color);
}
/* 헤더 */
.header {
  padding: 16px 18px; border-radius: 18px;
  background: linear-gradient(135deg, #FDF2F8 0%, #EEF2FF 100%);
  border: 1px solid rgba(0,0,0,0.06);
  display:flex; align-items:center; gap:12px; margin-bottom: 12px;
}
.header-emoji { font-size: 28px; }
.header h2 { margin:0; }
/* 카드 */
.metric-card {
  padding: 14px 16px; border-radius: 16px; background: var(--card-bg);
  border: 1px solid rgba(0,0,0,0.06);
}
/* 칩 */
.chip { display:inline-block; padding:4px 10px; border-radius:999px; font-weight:600; font-size:12px; }
.chip-green { background:var(--chip-green-bg); color:var(--chip-green-fg); border:1px solid var(--chip-green-bd); }
.chip-gray  { background:var(--chip-gray-bg);  color:var(--chip-gray-fg);  border:1px solid var(--chip-gray-bd); }
/* 입력창 크게 */
.big-input input[type="text"] { font-size:22px !important; padding:14px 12px !important; height:56px; }
/* 테이블 hover */
tbody tr:hover { background:#FAFAFA; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────
# 사용할 엑셀 파일명
# ──────────────────────────────
FILES = {"1부": "1부_여자.xlsx", "2부": "2부_여자.xlsx"}

# ──────────────────────────────
# 엑셀 안전 읽기/쓰기
# ──────────────────────────────
def safe_read_excel(path):
    if not os.path.exists(path):
        return pd.DataFrame(columns=["학번","이름","입장 여부","입장 시간"])
    df = pd.read_excel(path, engine="openpyxl")

    id_col = next((c for c in df.columns if ("학번" in str(c)) or (str(c).lower() in ["id","student_id"])), None)
    name_col = next((c for c in df.columns if ("이름" in str(c)) or (str(c).lower() in ["name","student_name"])), None)
    if id_col is None or name_col is None:
        raise ValueError("엑셀에 '학번' 또는 '이름' 컬럼이 없습니다.")

    out = df[[id_col, name_col]].copy()
    out.columns = ["학번","이름"]
    out["학번"] = out["학번"].astype(str).str.strip()
    out["이름"] = out["이름"].astype(str).str.strip()
    out["입장 여부"] = df["입장 여부"].fillna(0).astype(int) if "입장 여부" in df.columns else 0
    out["입장 시간"] = df["입장 시간"].fillna("").astype(str) if "입장 시간" in df.columns else ""
    return out

def safe_write_excel(df, path):
    dirn = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(dirn, exist_ok=True)
    tmpfile = tempfile.NamedTemporaryFile(delete=False, dir=dirn, suffix=".xlsx").name
    try:
        df.to_excel(tmpfile, index=False, engine="openpyxl")
        move(tmpfile, path)
    finally:
        if os.path.exists(tmpfile):
            try: os.remove(tmpfile)
            except: pass

def reset_df(df):
    df["입장 여부"] = 0
    df["입장 시간"] = ""
    return df

# 칩 렌더링
def style_attendance(df):
    disp = df.copy()
    disp["입장 표시"] = disp["입장 여부"].map(
        lambda x: '<span class="chip chip-green">출석</span>' if int(x)==1
                  else '<span class="chip chip-gray">미출석</span>'
    )
    return disp[["학번","이름","입장 표시","입장 시간"]]

# ──────────────────────────────
# Sidebar
# ──────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    available_parts = [p for p, f in FILES.items() if os.path.exists(f)] or list(FILES.keys())
    part = st.selectbox("부 선택", available_parts, index=0)
    st.caption("엑셀 파일은 앱 폴더에 두세요. (열 이름: 학번, 이름)")
    st.markdown("---")
    query = st.text_input("이름/학번 검색", value="")
    st.caption("관리자 초기화는 하단 ‘🛠️ 관리자’에서")

# ──────────────────────────────
# Header + 빠른 초기화 버튼
# ──────────────────────────────
st.markdown(f"""
<div class="header">
  <div class="header-emoji">🧸</div>
  <div>
    <h2>입장 체크 시스템 <small style="opacity:.7">({part})</small></h2>
    <div style="opacity:.7">학번 또는 이름 입력 → 즉시 입장</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────
# 데이터 로드
# ──────────────────────────────
FILE_PATH = FILES[part]
try:
    df = safe_read_excel(FILE_PATH)
except Exception as e:
    st.error(f"파일 읽기 오류: {e}")
    st.stop()

# 상단 빠른 초기화(현재 부만)
col_reset, col_sp = st.columns([1, 5])
with col_reset:
    if st.button("🧹 오늘 종료: 현재 부 입장 초기화"):
        df = reset_df(df)
        safe_write_excel(df, FILE_PATH)
        st.success(f"{part} 입장이 초기화되었습니다.")

# ──────────────────────────────
# 메트릭 카드
# ──────────────────────────────
total = len(df)
attended = int((df["입장 여부"] == 1).sum())
absent = total - attended
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="metric-card"><div>총원</div><h3>{total}</h3></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card"><div>입장장</div><h3>{attended}</h3></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card"><div>미입장</div><h3>{absent}</h3></div>', unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────
# 체크인 폼 — 학번 or 이름 입력 가능 (풍선 제거)
# ──────────────────────────────
st.markdown("#### ✅ 현장 체크인")
with st.form("checkin_form", clear_on_submit=True):
    st.markdown('<div class="big-input">', unsafe_allow_html=True)
    user_input = st.text_input("학번 또는 이름 입력", value="", help="학번 또는 이름 입력 후 Enter")
    st.markdown('</div>', unsafe_allow_html=True)
    submitted = st.form_submit_button("입장하기")

    if submitted:
        keyword = str(user_input).strip()
        if not keyword:
            st.warning("학번 또는 이름을 입력하세요.")
        else:
            df["학번"] = df["학번"].astype(str).str.strip()
            df["이름"] = df["이름"].astype(str).str.strip()

            # 정확 일치 우선 (학번 또는 이름)
            match = df[(df["학번"] == keyword) | (df["이름"] == keyword)]

            if match.empty:
                st.error("❌ 미신청자(명단에 없음)")
            else:
                idx = match.index[0]
                name = df.loc[idx, "이름"]
                if int(df.loc[idx, "입장 여부"]) == 1:
                    st.warning(f"⚠️ 이미 입장: {name}")
                else:
                    df.loc[idx, "입장 여부"] = 1
                    df.loc[idx, "입장 시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        safe_write_excel(df, FILE_PATH)
                        st.success(f"✅ 입장 완료: {name}")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

st.markdown("---")

# ──────────────────────────────
# 출석 현황
# ──────────────────────────────
st.markdown("#### 👀 출석 현황")
table_df = df.copy()
q = (query or "").strip().lower()
if q:
    mask = table_df["학번"].str.lower().str.contains(q) | table_df["이름"].str.lower().str.contains(q)
    table_df = table_df[mask]

styled = style_attendance(table_df)
st.write(styled.to_html(escape=False, index=False), unsafe_allow_html=True)

# 다운로드(백업)
st.download_button(
    "📥 현재 현황 CSV 다운로드",
    data=df[["학번","이름","입장 여부","입장 시간"]].to_csv(index=False).encode("utf-8-sig"),
    file_name=f"{part}_입장현황.csv",
    type="secondary"
)

# ──────────────────────────────
# 관리자 옵션 (기존 유지)
# ──────────────────────────────
with st.expander("🛠️ 관리자"):
    pwd = st.text_input("비밀번호", type="password", placeholder="기본값: admin")
    if st.button("이 부 전체 미출석으로 초기화"):
        if pwd == "admin":
            df = reset_df(df)
            safe_write_excel(df, FILE_PATH)
            st.success("초기화 완료")
        else:
            st.error("비밀번호 불일치")




