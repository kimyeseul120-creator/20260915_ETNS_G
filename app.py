"""
ETNS TODO APP
간단한 할 일 관리 웹앱 (Flask + SQLite / Supabase-Postgres)

- 환경변수 DATABASE_URL이 설정되어 있으면 Supabase(Postgres)를 사용합니다.
- 설정되어 있지 않으면 기존처럼 로컬 SQLite(todo.db)를 사용합니다.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash

try:
    # 로컬 실행 시 .env 파일의 DATABASE_URL 등을 자동으로 읽어옵니다.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

# Supabase 연결 문자열 (Vercel 환경변수 또는 로컬 .env에 설정)
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

    PH = "%s"  # Postgres 파라미터 플레이스홀더
else:
    # Vercel의 서버리스 환경은 프로젝트 폴더가 읽기 전용이고, /tmp만 쓰기가 가능합니다.
    # (단, /tmp는 요청마다 초기화될 수 있어 DATABASE_URL 없이 Vercel에 배포하면
    #  데이터가 영구 저장되지 않습니다. Supabase 연결을 권장하는 이유입니다.)
    if os.environ.get("VERCEL"):
        DB_PATH = Path("/tmp/todo.db")
    else:
        DB_PATH = BASE_DIR / "todo.db"
    PH = "?"  # SQLite 파라미터 플레이스홀더

app = Flask(__name__)
app.secret_key = "etns-todo-secret-key"  # 실습용 시크릿 키 (운영 배포 시 반드시 변경)


def get_db_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(conn, sql, params=(), fetch=None):
    """SQLite / Postgres(Supabase) 겸용 쿼리 실행 헬퍼."""
    if USE_POSTGRES:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(sql, params)

    result = None
    if fetch == "all":
        result = cur.fetchall()
    elif fetch == "one":
        result = cur.fetchone()

    cur.close()
    return result


def init_db():
    conn = get_db_connection()
    if USE_POSTGRES:
        run_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """,
        )
    else:
        run_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """,
        )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db_connection()
    todos = run_query(
        conn, "SELECT * FROM todos ORDER BY done ASC, id DESC", fetch="all"
    )
    conn.close()

    total = len(todos)
    done_count = sum(1 for t in todos if t["done"])

    return render_template(
        "index.html", todos=todos, total=total, done_count=done_count
    )


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if not title:
        flash("할 일 내용을 입력해주세요.")
        return redirect(url_for("index"))

    conn = get_db_connection()
    run_query(
        conn,
        f"INSERT INTO todos (title, done, created_at) VALUES ({PH}, 0, {PH})",
        (title, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    conn = get_db_connection()
    todo = run_query(
        conn, f"SELECT * FROM todos WHERE id = {PH}", (todo_id,), fetch="one"
    )
    if todo:
        run_query(
            conn,
            f"UPDATE todos SET done = {PH} WHERE id = {PH}",
            (0 if todo["done"] else 1, todo_id),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    conn = get_db_connection()
    run_query(conn, f"DELETE FROM todos WHERE id = {PH}", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    title = request.form.get("title", "").strip()
    if title:
        conn = get_db_connection()
        run_query(
            conn, f"UPDATE todos SET title = {PH} WHERE id = {PH}", (title, todo_id)
        )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


# Vercel 등 서버리스 환경에서는 __main__ 블록이 실행되지 않고 이 모듈이 바로
# import되어 app(WSGI 객체)만 사용되므로, 모듈 로드 시점에 DB를 초기화합니다.
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
