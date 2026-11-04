import json
import re

import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from auth import create_token, current_user, hash_password, verify_password
from db.postgres import get_conn

router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Credentials(BaseModel):
    email: str
    password: str


class ReportIn(BaseModel):
    topic: str
    report: str
    citations: list = []


def _normalize_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise HTTPException(400, "Please enter a valid email address")
    return email


# ---------------------------------------------------------------- auth
@router.post("/auth/register")
async def register(body: Credentials):
    email = _normalize_email(body.email)
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if len(body.password.encode()) > 72:  # bcrypt limit
        raise HTTPException(400, "Password is too long (max 72 characters)")

    pw_hash = await run_in_threadpool(hash_password, body.password)

    def _insert():
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                        (email, pw_hash))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return None
        finally:
            conn.close()

    user_id = await run_in_threadpool(_insert)
    if user_id is None:
        raise HTTPException(409, "An account with this email already exists")
    return {"token": create_token(user_id), "user": {"id": user_id, "email": email}}


@router.post("/auth/login")
async def login(body: Credentials):
    email = body.email.strip().lower()

    def _find():
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            return cur.fetchone()
        finally:
            conn.close()

    row = await run_in_threadpool(_find)
    ok = await run_in_threadpool(verify_password, body.password, row[1] if row else None)
    if not row or not ok:
        raise HTTPException(401, "Incorrect email or password")
    return {"token": create_token(row[0]), "user": {"id": row[0], "email": email}}


@router.get("/auth/me")
async def me(user: dict = Depends(current_user)):
    return {"user": user}


# ------------------------------------------------------------- reports
def _row_to_report(r):
    return {"id": str(r[0]), "topic": r[1], "report": r[2], "citations": r[3],
            "createdAt": r[4].isoformat()}


@router.get("/reports")
async def list_reports(user: dict = Depends(current_user)):
    def _q():
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT id, topic, report, citations, created_at FROM reports
                           WHERE user_id = %s ORDER BY created_at DESC LIMIT 200""", (user["id"],))
            return [_row_to_report(r) for r in cur.fetchall()]
        finally:
            conn.close()
    return {"reports": await run_in_threadpool(_q)}


@router.post("/reports")
async def save_report(body: ReportIn, user: dict = Depends(current_user)):
    if not body.report.strip():
        raise HTTPException(400, "Report is empty")

    def _ins():
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO reports (user_id, topic, report, citations)
                           VALUES (%s, %s, %s, %s::jsonb)
                           RETURNING id, topic, report, citations, created_at""",
                        (user["id"], body.topic.replace("\x00", "")[:500],
                         body.report.replace("\x00", ""), json.dumps(body.citations)))
            row = cur.fetchone()
            conn.commit()
            return _row_to_report(row)
        finally:
            conn.close()
    return await run_in_threadpool(_ins)


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, user: dict = Depends(current_user)):
    def _del():
        conn = get_conn()
        try:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM reports WHERE id = %s AND user_id = %s", (report_id, user["id"]))
            except psycopg2.errors.InvalidTextRepresentation:  # not a valid UUID
                conn.rollback()
                return 0
            n = cur.rowcount
            conn.commit()
            return n
        finally:
            conn.close()
    if await run_in_threadpool(_del) == 0:
        raise HTTPException(404, "Report not found")
    return {"status": "deleted"}