"""
ETNS TODO APP
간단한 할 일 관리 웹앱 (Flask + SQLite / Supabase-Postgres)

- 환경변수 DATABASE_URL이 설정되어 있으면 Supabase(Postgres)를 사용합니다.
- 설정되어 있지 않으면 기존처럼 로컬 SQLite(todo.db)를 사용합니다.
- 여러 사용자가 각자 회원가입/로그인해서, 본인의 할 일 목록만 보고 관리합니다.
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

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
# 실습용 시크릿 키. 세션(로그인 유지)을 암호화하는 데 쓰이므로, 운영 배포 시에는
# 환경변수(SECRET_KEY)로 바꿔서 사용하는 것을 권장합니다.
app.secret_key = os.environ.get("SECRET_KEY", "etns-todo-secret-key")


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
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        run_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """,
        )
        # 로그인 기능 추가 전에 만들어진 todos 테이블에는 user_id 컬럼이 없을 수 있으므로 보강합니다.
        run_query(conn, "ALTER TABLE todos ADD COLUMN IF NOT EXISTS user_id INTEGER")
    else:
        run_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        run_query(
            conn,
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """,
        )
        # SQLite는 "ADD COLUMN IF NOT EXISTS"를 지원하지 않으므로 직접 확인 후 추가합니다.
        existing_cols = [
            row["name"] for row in run_query(conn, "PRAGMA table_info(todos)", fetch="all")
        ]
        if "user_id" not in existing_cols:
            run_query(conn, "ALTER TABLE todos ADD COLUMN user_id INTEGER")
    conn.commit()
    conn.close()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


# ---------------- 회원가입 / 로그인 / 로그아웃 ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not username or not password:
        flash("아이디와 비밀번호를 모두 입력해주세요.")
        return redirect(url_for("register"))
    if password != password_confirm:
        flash("비밀번호가 서로 일치하지 않습니다.")
        return redirect(url_for("register"))
    if len(password) < 4:
        flash("비밀번호는 4자 이상 입력해주세요.")
        return redirect(url_for("register"))

    conn = get_db_connection()
    existing = run_query(
        conn, f"SELECT id FROM users WHERE username = {PH}", (username,), fetch="one"
    )
    if existing:
        conn.close()
        flash("이미 사용 중인 아이디입니다.")
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password)
    run_query(
        conn,
        f"INSERT INTO users (username, password_hash, created_at) VALUES ({PH}, {PH}, {PH})",
        (username, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()

    new_user = run_query(
        conn, f"SELECT id FROM users WHERE username = {PH}", (username,), fetch="one"
    )
    conn.close()

    session["user_id"] = new_user["id"]
    session["username"] = username
    flash(f"{username}님, 가입을 환영합니다!")
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = get_db_connection()
    user = run_query(
        conn, f"SELECT * FROM users WHERE username = {PH}", (username,), fetch="one"
    )
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        flash("아이디 또는 비밀번호가 올바르지 않습니다.")
        return redirect(url_for("login"))

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- 할 일 목록 (로그인 필요) ----------------

@app.route("/")
@login_required
def index():
    conn = get_db_connection()
    todos = run_query(
        conn,
        f"SELECT * FROM todos WHERE user_id = {PH} ORDER BY done ASC, id DESC",
        (session["user_id"],),
        fetch="all",
    )
    conn.close()

    total = len(todos)
    done_count = sum(1 for t in todos if t["done"])

    return render_template(
        "index.html",
        todos=todos,
        total=total,
        done_count=done_count,
        username=session.get("username"),
    )


@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title", "").strip()
    if not title:
        flash("할 일 내용을 입력해주세요.")
        return redirect(url_for("index"))

    conn = get_db_connection()
    run_query(
        conn,
        f"INSERT INTO todos (user_id, title, done, created_at) VALUES ({PH}, {PH}, 0, {PH})",
        (session["user_id"], title, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
@login_required
def toggle(todo_id):
    conn = get_db_connection()
    todo = run_query(
        conn,
        f"SELECT * FROM todos WHERE id = {PH} AND user_id = {PH}",
        (todo_id, session["user_id"]),
        fetch="one",
    )
    if todo:
        run_query(
            conn,
            f"UPDATE todos SET done = {PH} WHERE id = {PH} AND user_id = {PH}",
            (0 if todo["done"] else 1, todo_id, session["user_id"]),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
@login_required
def delete(todo_id):
    conn = get_db_connection()
    run_query(
        conn,
        f"DELETE FROM todos WHERE id = {PH} AND user_id = {PH}",
        (todo_id, session["user_id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
@login_required
def edit(todo_id):
    title = request.form.get("title", "").strip()
    if title:
        conn = get_db_connection()
        run_query(
            conn,
            f"UPDATE todos SET title = {PH} WHERE id = {PH} AND user_id = {PH}",
            (title, todo_id, session["user_id"]),
        )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


# Vercel 등 서버리스 환경에서는 __main__ 블록이 실행되지 않고 이 모듈이 바로
# import되어 app(WSGI 객체)만 사용되므로, 모듈 로드 시점에 DB를 초기화합니다.
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
