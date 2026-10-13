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

st.set_page_config(page_title="Event AI | 행사장 설계 스튜디오", page_icon="🎪", layout="wide")

# Korean font fallback: hosted environments may not include Korean fonts.
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
    # Top face
    poly3(ax, [(x,y,h),(x+w,y,h),(x+w,y+d,h),(x,y+d,h)], color, zorder=6)
    # Front and side faces create a raised architectural model effect
    shade = "#000000"
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
    # Site boundary and ground slab
    poly3(ax, [(0,0,0),(width,0,0),(width,depth,0),(0,depth,0)],
          "#E9ECE8", edge="#66727A", lw=1.7, zorder=0)

    # Road / perimeter access
    poly3(ax, [(-1.8,-1.5,0),(width+1.8,-1.5,0),(width+1.8,0,0),(-1.8,0,0)],
          "#737B80", edge="#555D62", zorder=1)
    # Main central circulation spine and cross aisle
    poly3(ax, [(width*.44,0,0),(width*.56,0,0),(width*.56,depth,0),(width*.44,depth,0)],
          "#F8F8F4", edge="#D0D5D8", zorder=1)
    poly3(ax, [(0,depth*.46,0),(width,depth*.46,0),(width,depth*.54,0),(0,depth*.54,0)],
          "#F8F8F4", edge="#D0D5D8", zorder=1)

    # Soft landscaping blocks
    for x,y,w,d in [(1,1,3,2),(width-4,1,3,2),(1,depth-3,3,2),(width-4,depth-3,3,2)]:
        if x+w < width and y+d < depth:
            poly3(ax, [(x,y,0),(x+w,y,0),(x+w,y+d,0),(x,y+d,0)], "#CFE3C8", edge="#A4C69A", zorder=2)
            for tx,ty in [(x+.6,y+.6),(x+w-0.6,y+d-0.6)]:
                px,py=project(tx,ty,.18)
                ax.add_patch(Circle((px,py),.12,fc="#4B8B54",ec="#2F6F3A",lw=.5,zorder=4))

    # Main stage and audience zone
    block(ax, width*.35, depth*.77, width*.30, depth*.13, 1.1, COLORS["무대"], "MAIN STAGE", 9)
    poly3(ax, [(width*.20,depth*.49,0),(width*.80,depth*.49,0),
               (width*.80,depth*.75,0),(width*.20,depth*.75,0)],
          "#A8D5F0", edge="#4A9BCB", zorder=3)
    # Seating rows
    for row in range(5):
        yy = depth*.515 + row*depth*.043
        poly3(ax, [(width*.25,yy,0.05),(width*.75,yy,0.05),
                   (width*.75,yy+depth*.012,0.05),(width*.25,yy+depth*.012,0.05)],
              "#2376A8" if row%2==0 else "#3C91C0", edge="#D9EFFA", lw=.4, zorder=4)
    px,py=project(width*.5, depth*.62,.2)
    ax.text(px,py,"관람 구역",ha="center",va="center",fontsize=9,color="#FFFFFF",weight="bold",zorder=10)

    # Booth zones on left and right edges
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
        # small booth markers inside experience/partner/food zones
        if key in ("연대·협력존","체험존","푸드존"):
            for i in range(3):
                bx=x+.25+i*(w-.65)/2
                by=y+.28
                poly3(ax,[(bx,by,.39),(bx+.42,by,.39),(bx+.42,by+.34,.39),(bx,by+.34,.39)],
                      "#FFF8E9",edge="#9A6A39",lw=.5,zorder=8)

    # Gates and evacuation arrows (conceptual, not certified)
    gate_xs = [width*.15, width*.50, width*.85] if gates >= 3 else [width*.5]
    for idx,gx in enumerate(gate_xs):
        p1=project(gx,0,.08)
        p2=project(gx,-1.15,.08)
        ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=15,
                                     linewidth=2,color="#D92332",zorder=12))
        ax.text(p2[0],p2[1]-.32, "비상 출구" if idx else "주 출입구",
                ha="center",va="top",fontsize=7.5,color="#A31925",weight="bold",zorder=12)

    # Main access arrow from the rear
    p1=project(width*.5,depth+1.4,.1); p2=project(width*.5,depth-.1,.1)
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=17,
                                 linewidth=2.3,color="#1675C9",zorder=12))
    ax.text(p1[0],p1[1]+.15,"VIP / 물류 접근",ha="center",va="bottom",
            fontsize=8,color="#155A96",weight="bold",zorder=12)

    # Dimension line / north arrow
    ax.text(project(width*.93,depth*.94,0)[0],project(width*.93,depth*.94,0)[1]+1.0,
            "N ↑",fontsize=10,weight="bold",color="#344054",zorder=15)

    # Title and detail
    ax.text(.02,.97,name,transform=ax.transAxes,ha="left",va="top",
            fontsize=17,weight="bold",color="#182230")
    subtitle=f"{venue_type}  |  {width}m × {depth}m  |  예상 관람객 {visitors:,}명  |  콘셉트: {vibe}"
    ax.text(.02,.925,subtitle,transform=ax.transAxes,ha="left",va="top",
            fontsize=9,color="#586574")
    ax.text(.02,.035,
            "CONCEPT MASTERPLAN · 배치 참고용 시안 / 실제 설치 전 현장 실측 및 안전 전문가 검토 필요",
            transform=ax.transAxes,fontsize=8,color="#697586",ha="left",va="bottom")

    # Legend on right
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

def scorecard(visitors, width, depth, gates):
    area=width*depth
    density=visitors/max(area,1)
    safety=max(55,min(96,round(94 - max(0,density-0.5)*18 + min(gates,6)*1.2)))
    flow=max(55,min(95,round(91 - max(0,density-0.4)*16)))
    access=max(60,min(98,round(86 + min(gates,6)*2)))
    space=max(50,min(96,round(92 - density*14)))
    return {"안전 계획 지표":safety,"동선 계획 지표":flow,"접근성 지표":access,"공간 활용 지표":space}

if "history" not in st.session_state:
    st.session_state.history=[]
if "user" not in st.session_state:
    st.session_state.user="게스트"

with st.sidebar:
    st.markdown("## ✦ Event AI")
    st.caption("행사장 공간 기획 · 배치 시안")
    st.markdown("---")
    st.markdown("### 계정")
    username=st.text_input("프로젝트 사용자명",value=st.session_state.user)
    if st.button("사용자 적용",use_container_width=True):
        st.session_state.user=username.strip() or "게스트"
        st.success("현재 세션에 적용했어요.")
    st.markdown("---")
    st.markdown("**빠른 메뉴**")
    st.markdown("- 행사 조건 입력")
    st.markdown("- 설계도 미리보기")
    st.markdown("- 결과 이미지 다운로드")
    st.markdown("- 설계 기록(JSON) 다운로드")
    st.caption("데모 계정 기능이며, 실제 회원 DB/비밀번호 인증은 연결되어 있지 않습니다.")

st.title("🎪 Event AI — 행사장 설계 스튜디오")
st.write("행사 조건을 입력하면 구역 배치가 반영된 **아이소메트릭(입체 투시) 스타일 행사장 마스터플랜**을 생성합니다.")
st.info("이 앱은 Archisketch의 공간 설계 접근 방식과 제공된 참고 이미지를 영감으로 만든 독립형 시안 생성기입니다. Archisketch 서비스에 직접 연결되거나 실제 CAD/BIM 도면을 검증하는 도구는 아닙니다.")

with st.form("design_form"):
    st.subheader("1. 행사 기본 조건")
    c1,c2,c3=st.columns(3)
    with c1:
        event_name=st.text_input("행사명", "함께하는 미래 페스티벌")
        venue_type=st.selectbox("행사장 유형",["야외 광장","실내 컨벤션 홀","체육관","캠퍼스/학교","도심 거리"])
        indoor=venue_type in ["실내 컨벤션 홀","체육관"]
    with c2:
        visitors=st.number_input("예상 관람객 수",min_value=50,max_value=100000,step=250,value=5000)
        duration=st.selectbox("운영 시간",["3시간 이내","3~6시간","6~10시간","종일"])
        age=st.selectbox("주요 연령대",["전 연령","청소년·대학생","가족 단위","성인","시니어"])
    with c3:
        vibe=st.selectbox("원하는 분위기",["활기찬 페스티벌","차분한 힐링","전문적인 박람회","친환경·자연","미래지향적"])
        ticket=st.selectbox("입장료",["무료","유료","초대권"])
        gates=st.slider("출입구/대피 출구 개수",min_value=2,max_value=8,value=4)
    st.subheader("2. 공간 크기와 구성")
    a,b,c=st.columns(3)
    with a:
        width=st.slider("가로 길이 (m)",min_value=30,max_value=250,value=100,step=5)
    with b:
        depth=st.slider("세로 길이 (m)",min_value=30,max_value=250,value=80,step=5)
    with c:
        zone_count=st.slider("원하는 주요 구역 수",min_value=4,max_value=9,value=7)
    notes=st.text_area("추가 요구사항", "중앙 관람 구역을 확보하고, 푸드존과 휴식존을 분리하며, 응급의료 구역은 외부 접근이 쉬운 곳에 배치")
    submitted=st.form_submit_button("✨ 행사장 설계도 생성",use_container_width=True)

if "design" not in st.session_state:
    st.session_state.design = {
        "event_name":"함께하는 미래 페스티벌","venue_type":"야외 광장","visitors":5000,
        "vibe":"활기찬 페스티벌","width":100,"depth":80,"gates":4,"duration":"6~10시간",
        "age":"전 연령","ticket":"무료","notes":"중앙 관람 구역 확보","zone_count":7
    }

if submitted:
    st.session_state.design={
        "event_name":event_name,"venue_type":venue_type,"visitors":int(visitors),
        "vibe":vibe,"width":width,"depth":depth,"gates":gates,"duration":duration,
        "age":age,"ticket":ticket,"notes":notes,"zone_count":zone_count
    }
    st.session_state.history.append({"created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),**st.session_state.design})

d=st.session_state.design
st.markdown("---")
st.subheader("2. 생성된 행사장 마스터플랜")
fig=draw_plan(d["event_name"],d["venue_type"],d["width"],d["depth"],d["visitors"],d["vibe"],
              d["venue_type"] in ["실내 컨벤션 홀","체육관"],d["gates"],d["zone_count"])
st.pyplot(fig,use_container_width=True)
img=io.BytesIO()
fig.savefig(img,format="png",dpi=220,bbox_inches="tight",facecolor="white")
plt.close(fig)
st.download_button("⬇️ 행사장 설계도 PNG 다운로드",data=img.getvalue(),
                   file_name="event_masterplan.png",mime="image/png",use_container_width=True)

st.subheader("3. 설계 요약")
m1,m2,m3,m4=st.columns(4)
m1.metric("행사장 면적",f'{d["width"]*d["depth"]:,} m²')
m2.metric("예상 관람객",f'{d["visitors"]:,}명')
m3.metric("출입구/출구",f'{d["gates"]}개')
m4.metric("운영 시간",d["duration"])
scores=scorecard(d["visitors"],d["width"],d["depth"],d["gates"])
cols=st.columns(len(scores))
for col,(label,val) in zip(cols,scores.items()):
    col.metric(label,f"{val}/100")
st.caption("점수는 입력 조건을 바탕으로 한 데모용 휴리스틱 지표이며, 실제 안전성 인증이나 현장 검증 결과가 아닙니다.")

st.subheader("4. 배치 원칙 및 운영 체크리스트")
checks=[
    "주 출입구와 비상 출구를 서로 다른 방향에 분산 배치하는 안을 현장 여건과 함께 검토",
    "푸드존·체험존 대기열이 주 통로를 막지 않도록 대기 공간 별도 확보",
    "응급의료 구역에서 외부 진입로까지 장비와 차량이 접근할 수 있는 경로 확보",
    "화장실·휴식 공간은 주요 구역에서 찾기 쉽도록 안내 표지 계획",
    "실제 행사 전 관할 기관, 시설 관리자, 안전 담당자의 검토 및 현장 실측 진행"
]
for item in checks:
    st.checkbox(item,value=False,key="check_"+hashlib.md5(item.encode()).hexdigest()[:8])

export_data={**d,"generated_at":datetime.now().isoformat(timespec="minutes"),
             "area_m2":d["width"]*d["depth"],"demo_scores":scores,
             "zones":["무대","관람석","연대·협력존","체험존","푸드존","휴식존","운영본부","응급의료","화장실"],
             "additional_requirements":d["notes"]}
st.download_button("🧾 설계 조건 JSON 다운로드",
                   data=json.dumps(export_data,ensure_ascii=False,indent=2),
                   file_name="event_design.json",mime="application/json")
if st.session_state.history:
    with st.expander("🕘 현재 세션의 설계 기록"):
        st.dataframe(st.session_state.history,use_container_width=True)
        st.download_button("설계 기록 CSV 다운로드",
                           data=__import__("pandas").DataFrame(st.session_state.history).to_csv(index=False).encode("utf-8-sig"),
                           file_name="event_design_history.csv",mime="text/csv")
st.markdown("---")
st.caption("제작 목적: 행사 공간 기획을 돕는 교육·시안용 프로토타입. 실제 시공 도면, 피난 계획, 군중 안전 검토를 대체하지 않습니다.")
