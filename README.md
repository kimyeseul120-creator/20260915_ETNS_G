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

⚠️ **주의: DATABASE_URL 미설정 시 데이터 영구 저장 불가**
Vercel은 서버리스 환경이라 프로젝트 폴더가 읽기 전용이며, 쓰기 가능한 `/tmp` 영역도 요청/인스턴스마다 초기화될 수 있습니다.
아래 Supabase 연동을 하지 않으면, Vercel에 배포된 버전은 할 일 데이터가 영구적으로 저장되지 않고 수시로 초기화될 수 있습니다.

## Supabase(Postgres) 연동 안내

환경변수 `DATABASE_URL`이 설정되어 있으면 자동으로 SQLite 대신 Supabase Postgres를 사용합니다 (앱 코드 수정 불필요).

1. [supabase.com](https://supabase.com)에서 프로젝트 생성
2. Project Settings → Database → Connection string → **URI** 복사
   (Vercel 같은 서버리스 환경에서는 포트 `6543`의 **Connection pooling(Transaction mode)** 문자열 권장)
3. 로컬 실행 시: 프로젝트 루트에 `.env` 파일을 만들고 아래처럼 입력 (`.env.example` 참고, `.env`는 git에 올라가지 않음)
   ```
   DATABASE_URL=postgresql://postgres:비밀번호@호스트:6543/postgres
   ```
4. Vercel 배포본에 적용하려면: Vercel 프로젝트 → Settings → Environment Variables → `DATABASE_URL` 추가 후 **Redeploy**
5. 최초 요청 시 `todos` 테이블이 자동 생성됩니다 (별도 SQL 실행 불필요)

⚠️ `DATABASE_URL`에는 DB 비밀번호가 포함되어 있으니, 코드/커밋/채팅 등 어디에도 그대로 붙여넣지 말고 `.env` 파일과 Vercel 환경변수 설정에만 입력하세요.
