import io
import json
import math
import hashlib
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyArrowPatch
import streamlit as st
import streamlit.components.v1 as components

# Streamlit 페이지 설정
st.set_page_config(
    page_title="이벤트 온 (Event-On) - AI 행사 자동 설계 플랫폼",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Korean font fallback
plt.rcParams["axes.unicode_minus"] = False

COLORS = {
    "무대": "#2387C9", "관람석": "#1976B9", "연대·협력존": "#F4C542",
    "체험존": "#24B6AC", "푸드존": "#D94B4B", "휴식존": "#79B94B",
    "운영본부": "#8A69B4", "응급의료": "#F07832", "화장실": "#5DADE2",
    "부스": "#B96B2C", "통로": "#D7DADD"
}
ZONE_ICONS = {
    "무대":"★", "관람석":"▦", "연대·협력존":"◎", "체험존":"✋",
    "푸드존":"♨", "휴식존":"♧", "운영본부":"⚙", "응급의료":"✚", "화장실":"♙"
}

def project(x, y, z=0):
    """Simple axonometric projection for a presentation-style site plan."""
    return (x - y * 0.52, (x + y) * 0.28 - z)

def poly3(ax, pts, color, edge="#59636B", lw=0.9, alpha=1, zorder=2):
    projected = [project(*p) for p in pts]
    ax.add_patch(Polygon(projected, closed=True, facecolor=color, edgecolor=edge,
                         linewidth=lw, alpha=alpha, joinstyle="round", zorder=zorder))

def block(ax, x, y, w, d, h, color, label, fontsize=8):
    poly3(ax, [(x,y,h),(x+w,y,h),(x+w,y+d,h),(x,y+d,h)], color, zorder=6)
    front = [(x,y,0),(x+w,y,0),(x+w,y,h),(x,y,h)]
    side = [(x+w,y,0),(x+w,y+d,0),(x+w,y+d,h),(x+w,y,h)]
    poly3(ax, front, color, edge="#475569", zorder=4)
    poly3(ax, side, "#8B969E" if color != "#8B969E" else "#68747D", edge="#475569", zorder=5)
    cx, cy = project(x+w/2, y+d/2, h+0.02)
    ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize,
            color="#17212B", weight="bold", zorder=10,
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=.82))

def draw_plan(name, venue_type, width, depth, visitors, vibe, indoor, gates, zone_count, include_labels=True):
    fig, ax = plt.subplots(figsize=(14, 8.2), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    poly3(ax, [(0,0,0),(width,0,0),(width,depth,0),(0,depth,0)],
          "#E9ECE8", edge="#66727A", lw=1.7, zorder=0)

    poly3(ax, [(-1.8,-1.5,0),(width+1.8,-1.5,0),(width+1.8,0,0),(-1.8,0,0)],
          "#737B80", edge="#555D62", zorder=1)
    poly3(ax, [(width*.44,0,0),(width*.56,0,0),(width*.56,depth,0),(width*.44,depth,0)],
          "#F8F8F4", edge="#D0D5D8", zorder=1)
    poly3(ax, [(0,depth*.46,0),(width,depth*.46,0),(width,depth*.54,0),(0,depth*.54,0)],
          "#F8F8F4", edge="#D0D5D8", zorder=1)

    for x,y,w,d in [(1,1,3,2),(width-4,1,3,2),(1,depth-3,3,2),(width-4,depth-3,3,2)]:
        if x+w < width and y+d < depth:
            poly3(ax, [(x,y,0),(x+w,y,0),(x+w,y+d,0),(x,y+d,0)], "#CFE3C8", edge="#A4C69A", zorder=2)
            for tx,ty in [(x+.6,y+.6),(x+w-0.6,y+d-0.6)]:
                px,py=project(tx,ty,.18)
                ax.add_patch(Circle((px,py),.12,fc="#4B8B54",ec="#2F6F3A",lw=.5,zorder=4))

    block(ax, width*.35, depth*.77, width*.30, depth*.13, 1.1, COLORS["무대"], "MAIN STAGE", 9)
    poly3(ax, [(width*.20,depth*.49,0),(width*.80,depth*.49,0),
               (width*.80,depth*.75,0),(width*.20,depth*.75,0)],
          "#A8D5F0", edge="#4A9BCB", zorder=3)
    for row in range(5):
        yy = depth*.515 + row*depth*.043
        poly3(ax, [(width*.25,yy,0.05),(width*.75,yy,0.05),
                   (width*.75,yy+depth*.012,0.05),(width*.25,yy+depth*.012,0.05)],
              "#2376A8" if row%2==0 else "#3C91C0", edge="#D9EFFA", lw=.4, zorder=4)
    px,py=project(width*.5, depth*.62,.2)
    ax.text(px,py,"관람 구역",ha="center",va="center",fontsize=9,color="#FFFFFF",weight="bold",zorder=10)

    zone_specs = [
        ("연대·협력존", .06, .58, .22, .14, "PARTNERS"),
        ("체험존", .06, .36, .22, .14, "EXPERIENCE"),
        ("푸드존", .72, .58, .22, .14, "FOOD COURT"),
        ("휴식존", .72, .36, .22, .14, "REST GARDEN"),
        ("운영본부", .06, .12, .18, .13, "OPS"),
        ("응급의료", .76, .12, .18, .13, "MEDICAL"),
        ("화장실", .40, .10, .18, .10, "RESTROOM"),
    ]
    for key, rx, ry, rw, rd, label in zone_specs:
        x,y,w,d = width*rx, depth*ry, width*rw, depth*rd
        block(ax, x,y,w,d,.35,COLORS[key],label,7)
        if key in ("연대·협력존","체험존","푸드존"):
            for i in range(3):
                bx=x+.25+i*(w-.65)/2
                by=y+.28
                poly3(ax,[(bx,by,.39),(bx+.42,by,.39),(bx+.42,by+.34,.39),(bx,by+.34,.39)],
                      "#FFF8E9",edge="#9A6A39",lw=.5,zorder=8)

    gate_xs = [width*.15, width*.50, width*.85] if gates >= 3 else [width*.5]
    for idx,gx in enumerate(gate_xs):
        p1=project(gx,0,.08)
        p2=project(gx,-1.15,.08)
        ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=15,
                                     linewidth=2,color="#D92332",zorder=12))
        ax.text(p2[0],p2[1]-.32, "비상 출구" if idx else "주 출입구",
                ha="center",va="top",fontsize=7.5,color="#A31925",weight="bold",zorder=12)

    p1=project(width*.5,depth+1.4,.1); p2=project(width*.5,depth-.1,.1)
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=17,
                                 linewidth=2.3,color="#1675C9",zorder=12))
    ax.text(p1[0],p1[1]+.15,"VIP / 물류 접근",ha="center",va="bottom",
            fontsize=8,color="#155A96",weight="bold",zorder=12)

    ax.text(project(width*.93,depth*.94,0)[0],project(width*.93,depth*.94,0)[1]+1.0,
            "N ↑",fontsize=10,weight="bold",color="#344054",zorder=15)

    ax.text(.02,.97,name,transform=ax.transAxes,ha="left",va="top",
            fontsize=17,weight="bold",color="#182230")
    subtitle=f"{venue_type}  |  {width}m × {depth}m  |  예상 관람객 {visitors:,}명  |  콘셉트: {vibe}"
    ax.text(.02,.925,subtitle,transform=ax.transAxes,ha="left",va="top",
            fontsize=9,color="#586574")
    ax.text(.02,.035,
            "CONCEPT MASTERPLAN · 배치 참고용 시안 / 실제 설치 전 현장 실측 및 안전 전문가 검토 필요",
            transform=ax.transAxes,fontsize=8,color="#697586",ha="left",va="bottom")

    legend_items = ["무대","관람석","연대·협력존","체험존","푸드존","휴식존","운영본부","응급의료","화장실"]
    handles=[]
    for item in legend_items:
        handles.append(Rectangle((0,0),1,1,facecolor=COLORS[item],edgecolor="#FFFFFF",label=item))
    ax.legend(handles=handles,loc="center left",bbox_to_anchor=(1.005,.5),frameon=False,
              fontsize=8,title="구역 범례",title_fontsize=10)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=.02,right=.83,top=.98,bottom=.03)
    return fig

# 커스텀 스타일 정의 (사이드바 상단 고정 및 하단 고정 완벽 적용)
st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    .custom-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .badge-excellent { background-color: #DCFCE7; color: #15803D; }
    .badge-good { background-color: #DBEAFE; color: #1E40AF; }
    .badge-warning { background-color: #FEF3C7; color: #B45309; }
    .reason-box {
        background-color: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 16px;
        border-radius: 12px;
        margin-top: 10px;
        color: #0F172A;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
    }
    /* 사이드바 메인보드 및 메뉴를 맨 위로 고정, 하단 프로필과 완벽 분리 */
    [data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 94vh;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = True
if 'username' not in st.session_state:
    st.session_state['username'] = "주은님"
if "history" not in st.session_state:
    st.session_state.history = []
if "design" not in st.session_state:
    st.session_state.design = {
        "event_name": "함께하는 미래 페스티벌", "venue_type": "야외 광장", "visitors": 5000,
        "vibe": "활기찬 페스티벌", "width": 100, "depth": 80, "gates": 4, "duration": "6~10시간",
        "age": "전 연령", "ticket": "무료", "notes": "중앙 관람 구역 확보", "zone_count": 7
    }

# 사이드바 구성 (메인보드/메뉴를 맨 위에 배치하고 프로필을 맨 아래로 고정)
with st.sidebar:
    with st.container():
        if st.button("🎪 이벤트 온 (Event-On)", key="logo_btn", use_container_width=True, type="primary"):
            st.session_state['page'] = 'home'
            st.rerun()

        st.caption("AI 기반 행사 공간 자동 설계 플랫폼")
        st.divider()
        
        if st.button("🏠 홈 (대시보드)", key="nav_home", use_container_width=True):
            st.session_state['page'] = 'home'
            st.rerun()
        if st.button("📐 행사장 설계 스튜디오", key="nav_studio", use_container_width=True):
            st.session_state['page'] = 'studio'
            st.rerun()
        if st.button("⚙️ AI 설계 프로세스", key="nav_process", use_container_width=True):
            st.session_state['page'] = 'process'
            st.rerun()

    with st.container():
        if st.session_state['logged_in']:
            st.markdown(f"👤 **{st.session_state['username']}** 님 (총괄 기획)")
            if st.button("로그아웃", key="sidebar_logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.rerun()

# 상단 헤더 영역
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.title("🎪 이벤트 온 (Event-On)")
with top_col2:
    st.markdown("<div style='text-align: right; padding-top: 10px;'>", unsafe_allow_html=True)
    if st.session_state['logged_in']:
        with st.popover(f"👤 {st.session_state['username']}"):
            st.write(f"**{st.session_state['username']}** (총괄 기획자)")
            st.caption("이메일: user@event-on.ai")
            st.divider()
            if st.button("설정 관리", key="pop_settings"):
                st.session_state['page'] = 'settings'
                st.rerun()
            if st.button("로그아웃", key="pop_logout"):
                st.session_state['logged_in'] = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ==========================================
# 1. 홈 화면 (Home Page - AI 어시스턴트 및 Archisketch 3D 뷰어 포함)
# ==========================================
if st.session_state['page'] == 'home':
    st.markdown("## 📊 AI 스마트 공간 설계 대시보드")
    st.caption("실시간 대화형 AI 어시스턴트와 Archisketch 3D 디지털 트윈 연동 시스템입니다.")
    st.markdown("<br>", unsafe_allow_html=True)

    # 4. AI 어시스턴트 입력창 상단 배치
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8fafc, #eff6ff); border: 1.5px solid #bfdbfe; border-radius: 16px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #1e3a8a; margin-top: 0; font-size: 1.15rem;">🤖 AI 메인 어시스턴트 (실시간 레이아웃 제어)</h3>
            <p style="color: #475569; font-size: 0.9rem; margin-bottom: 12px;">원하시는 부스 추가나 배치 수정 사항을 말씀해 주시면 디지털 트윈에 즉시 반영합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "ai", "content": "안녕하세요 주은님! 원하시는 부스 추가나 배치 수정 사항을 말씀해 주세요."}
            ]
        
        for msg in st.session_state.chat_history:
            if msg["role"] == "ai":
                st.info(f"**AI:** {msg['content']}")
            else:
                st.success(f"**나:** {msg['content']}")
                
        user_msg = st.text_input("AI에게 명령하기 (예: 친환경 팝업스토어 추가해줘)", key="main_ai_input_box")
        if st.button("AI 메시지 전송", key="send_main_ai"):
            if user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                st.session_state.chat_history.append({"role": "ai", "content": f'요청하신 "{user_msg}" 내용을 분석하여 배치도 반영 시뮬레이션을 완료했습니다.'})
                st.rerun()

    st.markdown("---")

    # 5. 3D 디지털 트윈 공간: 요청하신 Archisketch 지도 링크 연동 iframe
    st.markdown("### 🧊 3D 디지털 트윈 뷰어 (Archisketch 연동)")
    st.caption("아키스케치(Archisketch) 플랫폼 공간 뷰어를 통해 실시간 3D 가상 공간을 체험할 수 있습니다.")
    components.iframe("https://maps.archisketch.com/", height=650, scrolling=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_dash, col_studio = st.columns(2)
    with col_dash:
        if st.button("📐 행사장 설계 스튜디오로 이동", key="btn_click_studio", type="primary", use_container_width=True):
            st.session_state['page'] = 'studio'
            st.rerun()
    with col_studio:
        if st.button("⚙️ AI 설계 프로세스 확인하기", key="btn_click_proc", type="secondary", use_container_width=True):
            st.session_state['page'] = 'process'
            st.rerun()

# ==========================================
# 2. 행사장 설계 스튜디오 (Studio Page)
# ==========================================
elif st.session_state['page'] == 'studio':
    st.markdown("## 📐 행사장 공간 기획 · 배치 시안 스튜디오")
    st.info("행사 조건을 입력하면 구역 배치가 반영된 **아이소메트릭(입체 투시) 스타일 행사장 마스터플랜**을 생성합니다.")

    with st.form("design_form"):
        st.subheader("1. 행사 기본 조건")
        c1, c2, c3 = st.columns(3)
        with c1:
            event_name = st.text_input("행사명", st.session_state.design["event_name"])
            venue_type = st.selectbox("행사장 유형", ["야외 광장", "실내 컨벤션 홀", "체육관", "캠퍼스/학교", "도심 거리"],
                                     index=["야외 광장", "실내 컨벤션 홀", "체육관", "캠퍼스/학교", "도심 거리"].index(st.session_state.design["venue_type"]))
            indoor = venue_type in ["실내 컨벤션 홀", "체육관"]
        with c2:
            visitors = st.number_input("예상 관람객 수", min_value=50, max_value=100000, step=250, value=st.session_state.design["visitors"])
            duration = st.selectbox("운영 시간", ["3시간 이내", "3~6시간", "6~10시간", "종일"],
                                     index=["3시간 이내", "3~6시간", "6~10시간", "종일"].index(st.session_state.design["duration"]))
            age = st.selectbox("주요 연령대", ["전 연령", "청소년·대학생", "가족 단위", "성인", "시니어"],
                                index=["전 연령", "청소년·대학생", "가족 단위", "성인", "시니어"].index(st.session_state.design["age"]))
        with c3:
            vibe = st.selectbox("원하는 분위기", ["활기찬 페스티벌", "차분한 힐링", "전문적인 박람회", "친환경·자연", "미래지향적"],
                                index=["활기찬 페스티벌", "차분한 힐링", "전문적인 박람회", "친환경·자연", "미래지향적"].index(st.session_state.design["vibe"]))
            ticket = st.selectbox("입장료", ["무료", "유료", "초대권"],
                                  index=["무료", "유료", "초대권"].index(st.session_state.design["ticket"]))
            gates = st.slider("출입구/대피 출구 개수", min_value=2, max_value=8, value=st.session_state.design["gates"])
        
        st.subheader("2. 공간 크기와 구성")
        a, b, c = st.columns(3)
        with a:
            width = st.slider("가로 길이 (m)", min_value=30, max_value=250, value=st.session_state.design["width"], step=5)
        with b:
            depth = st.slider("세로 길이 (m)", min_value=30, max_value=250, value=st.session_state.design["depth"], step=5)
        with c:
            zone_count = st.slider("원하는 주요 구역 수", min_value=4, max_value=9, value=st.session_state.design["zone_count"])
        
        notes = st.text_area("추가 요구사항", st.session_state.design["notes"])
        submitted = st.form_submit_button("✨ 행사장 설계도 생성", use_container_width=True)

    if submitted:
        st.session_state.design = {
            "event_name": event_name, "venue_type": venue_type, "visitors": int(visitors),
            "vibe": vibe, "width": width, "depth": depth, "gates": gates, "duration": duration,
            "age": age, "ticket": ticket, "notes": notes, "zone_count": zone_count
        }
        st.session_state.history.append({"created_at": datetime.now().strftime("%Y-%m-%d %H:%M"), **st.session_state.design})

    d = st.session_state.design
    st.markdown("---")
    st.subheader("2. 생성된 행사장 마스터플랜")
    fig = draw_plan(d["event_name"], d["venue_type"], d["width"], d["depth"], d["visitors"], d["vibe"],
                    d["venue_type"] in ["실내 컨벤션 홀", "체육관"], d["gates"], d["zone_count"])
    st.pyplot(fig, use_container_width=True)
    
    img = io.BytesIO()
    fig.savefig(img, format="png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    st.download_button("⬇️ 행사장 설계도 PNG 다운로드", data=img.getvalue(),
                       file_name="event_masterplan.png", mime="image/png", use_container_width=True)

    st.subheader("3. 설계 요약")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("행사장 면적", f'{d["width"]*d["depth"]:,} m²')
    m2.metric("예상 관람객", f'{d["visitors"]:,}명')
    m3.metric("출입구/출구", f'{d["gates"]}개')
    m4.metric("운영 시간", d["duration"])
    
    # 3. AI 평가 결과 & XAI 항목 완전 삭제 완료
    st.markdown("---")
    st.subheader("4. 배치 원칙 및 운영 체크리스트")
    checks = [
        "주 출입구와 비상 출구를 서로 다른 방향에 분산 배치하는 안을 현장 여건과 함께 검토",
        "푸드존·체험존 대기열이 주 통로를 막지 않도록 대기 공간 별도 확보",
        "화장실·휴식 공간은 주요 구역에서 찾기 쉽도록 안내 표지 계획",
        "실제 행사 전 관할 기관, 시설 관리자, 안전 담당자의 검토 및 현장 실측 진행"
    ]
    for item in checks:
        st.checkbox(item, value=False, key="check_" + hashlib.md5(item.encode()).hexdigest()[:8])

    export_data = {**d, "generated_at": datetime.now().isoformat(timespec="minutes"),
                   "area_m2": d["width"]*d["depth"],
                   "zones": ["무대", "관람석", "연대·협력존", "체험존", "푸드존", "휴식존", "운영본부", "응급의료", "화장실"],
                   "additional_requirements": d["notes"]}
    st.download_button("🧾 설계 조건 JSON 다운로드",
                       data=json.dumps(export_data, ensure_ascii=False, indent=2),
                       file_name="event_design.json", mime="application/json")
    
    if st.session_state.history:
        with st.expander("🕘 현재 세션의 설계 기록"):
            st.dataframe(st.session_state.history, use_container_width=True)
            st.download_button("설계 기록 CSV 다운로드",
                               data=__import__("pandas").DataFrame(st.session_state.history).to_csv(index=False).encode("utf-8-sig"),
                               file_name="event_design_history.csv", mime="text/csv")

# ==========================================
# 3. AI 설계 프로세스 화면 (Process Page)
# ==========================================
elif st.session_state['page'] == 'process':
    st.markdown("## ⚙️ AI 행사 설계 프로세스 (Workflow)")
    st.caption("기획부터 최종 최적화 설계안 도출까지의 전체 운영 흐름도입니다.")

    col_w1, col_w2, col_w3, col_w4 = st.columns(4)
    with col_w1:
        st.markdown("""
            <div class="custom-card" style="text-align: center; min-height: 200px;">
                <h3>📋</h3>
                <h4>1단계: 정보 입력</h4>
                <p style="font-size: 0.85rem; color: #64748B;">예산, 목적, 예상 관람객 및 맞춤 부스 요구사항 입력</p>
            </div>
        """, unsafe_allow_html=True)
    with col_w2:
        st.markdown("""
            <div class="custom-card" style="text-align: center; min-height: 200px;">
                <h3>🌐</h3>
                <h4>2단계: 디지털 트윈</h4>
                <p style="font-size: 0.85rem; color: #64748B;">장소 지형 데이터를 바탕으로 3D 가상 공간 구축</p>
            </div>
        """, unsafe_allow_html=True)
    with col_w3:
        st.markdown("""
            <div class="custom-card" style="text-align: center; min-height: 200px;">
                <h3>🤖</h3>
                <h4>3단계: 자동 배치</h4>
                <p style="font-size: 0.85rem; color: #64748B;">수천 개의 행사 배치안 및 강화학습 시뮬레이션 수행</p>
            </div>
        """, unsafe_allow_html=True)
    with col_w4:
        st.markdown("""
            <div class="custom-card" style="text-align: center; min-height: 200px;">
                <h3>📄</h3>
                <h4>4단계: 최종 리포트</h4>
                <p style="font-size: 0.85rem; color: #64748B;">최종 비교 리포트 및 마스터플랜 도면 출력</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **운영자 기대 효과:** 운영자는 객관적인 데이터를 기반으로 안전하고 효율적인 대규모 행사를 신속하게 기획할 수 있습니다.")

# ==========================================
# 4. 시스템 설정 화면 (Settings Page)
# ==========================================
elif st.session_state['page'] == 'settings':
    st.markdown("## ⚙️ 시스템 설정 및 관리")

    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("👤 계정 및 사용자 프로필")
        st.session_state['username'] = st.text_input("사용자 이름", value=st.session_state['username'])
        st.text_input("소속 부서 / 조직", value="이벤트 기획 1팀")
        st.text_input("이메일 주소", value="user@event-on.ai")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("🖥️ AI 디지털 트윈 엔진 옵션")
        st.toggle("도면 내 레이블 및 좌표 가이드 표시", value=True)
        st.toggle("실시간 군중 시뮬레이션 자동 실행", value=True)
        st.selectbox("AI 추론 모델 선택", ["EventOn-Engine v4.2 (최신/권장)", "EventOn-Lite"])
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("로그아웃", type="primary"):
        st.session_state['logged_in'] = False
        st.session_state['page'] = 'home'
        st.rerun()
