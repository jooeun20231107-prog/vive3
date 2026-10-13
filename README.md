# Event AI — 행사장 설계 스튜디오

행사 조건을 입력하면 입체 투시 스타일의 행사장 배치 시안을 생성하는 Streamlit 프로젝트입니다.

## 기능
- 행사명, 유형, 관람객 수, 운영 시간, 연령대, 분위기, 입장료 입력
- 행사장 가로·세로 크기와 출입구 수 설정
- 구역별 배치 시안 생성: 무대, 관람 구역, 체험존, 푸드존, 휴식존, 운영본부, 응급의료, 화장실
- PNG 설계도 다운로드
- 설계 조건 JSON 및 세션 기록 CSV 다운로드
- 데모용 계획 지표와 운영 체크리스트

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub에 올리기
1. 새 GitHub 저장소를 만듭니다.
2. `app.py`, `requirements.txt`, `README.md`를 업로드합니다.
3. Streamlit Community Cloud에서 GitHub 저장소를 연결하고 메인 파일을 `app.py`로 지정합니다.

## 중요한 한계
이 프로젝트는 참고 이미지와 Archisketch의 공간 설계 개념에서 영감을 얻은 독립형 시안 생성기입니다. Archisketch 서비스/API에 직접 연결하지 않습니다. 로그인은 세션용 데모이며 실제 계정 인증/DB는 없습니다. 점수는 시연용 추정치로 안전 인증이 아니며, 실제 행사에는 현장 실측 및 자격 있는 안전 담당자의 검토가 필요합니다.
