"""
ETNS TODO APP
간단한 할 일 관리 웹앱 (Flask + SQLite)
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todo.db"

app = Flask(__name__)
app.secret_key = "etns-todo-secret-key"  # 실습용 시크릿 키 (운영 배포 시 반드시 변경)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db_connection()
    todos = conn.execute(
        "SELECT * FROM todos ORDER BY done ASC, id DESC"
    ).fetchall()
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
    conn.execute(
        "INSERT INTO todos (title, done, created_at) VALUES (?, 0, ?)",
        (title, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    conn = get_db_connection()
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if todo:
        conn.execute(
            "UPDATE todos SET done = ? WHERE id = ?",
            (0 if todo["done"] else 1, todo_id),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    title = request.form.get("title", "").strip()
    if title:
        conn = get_db_connection()
        conn.execute("UPDATE todos SET title = ? WHERE id = ?", (title, todo_id))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
