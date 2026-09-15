# ETNS TODO APP

Python Flask로 만든 간단한 할 일 관리 웹앱입니다.

## 기능
- 할 일 추가 / 수정 / 삭제
- 완료 / 미완료 체크
- SQLite 데이터베이스에 자동 저장 (앱을 껐다 켜도 데이터 유지)

## 실행 방법

1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

2. 앱 실행

```bash
python app.py
```

3. 브라우저에서 접속

```
http://127.0.0.1:5000
```

## 폴더 구조

```
ETNS_TODO_APP/
├── app.py              # Flask 서버 (라우팅, DB 처리)
├── requirements.txt    # 필요 패키지 목록
├── templates/
│   └── index.html      # 메인 화면
├── static/
│   └── style.css        # 스타일시트
└── todo.db             # 실행 시 자동 생성되는 SQLite DB
```
