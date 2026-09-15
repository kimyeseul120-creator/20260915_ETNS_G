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
├── vercel.json         # Vercel 배포 설정
├── templates/
│   └── index.html      # 메인 화면
├── static/
│   └── style.css        # 스타일시트
└── todo.db             # 실행 시 자동 생성되는 SQLite DB
```

## Vercel 배포 안내

이 저장소는 `vercel.json`을 통해 Vercel의 Python 런타임(`@vercel/python`)으로 배포됩니다.

⚠️ **주의: 데이터 영구 저장 불가**
Vercel은 서버리스 환경이라 프로젝트 폴더가 읽기 전용이며, 쓰기 가능한 `/tmp` 영역도 요청/인스턴스마다 초기화될 수 있습니다.
따라서 Vercel에 배포된 버전은 **로컬 실행과 달리 할 일 데이터가 영구적으로 저장되지 않고 수시로 초기화될 수 있습니다** (데모/실습용).
데이터를 계속 유지하려면 Vercel Postgres, Supabase 등 외부 DB 연동이 필요합니다.
