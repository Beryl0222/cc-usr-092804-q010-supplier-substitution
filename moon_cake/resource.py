"""resource 领域模块，保存可审计的业务规则。"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Iterable

MODULE = "moon_cake.resource"

@dataclass(frozen=True)
class MoonCakeResourceRecord:
    key: str
    subject: str
    state: str
    version: int
    actor: str
    effective_at: str
    payload: dict[str, Any]

class MoonCakeResourceError(Exception):
    """领域校验错误。"""

class MoonCakeResourceStore:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS moon_cake_resource_records(
            key TEXT PRIMARY KEY, subject TEXT NOT NULL, state TEXT NOT NULL,
            version INTEGER NOT NULL, actor TEXT NOT NULL, effective_at TEXT NOT NULL,
            payload TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS moon_cake_resource_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL, action TEXT NOT NULL,
            request_id TEXT NOT NULL, actor TEXT NOT NULL, before_state TEXT,
            after_state TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL,
            UNIQUE(key, request_id))""")
        self.db.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get(self, key: str) -> MoonCakeResourceRecord | None:
        row = self.db.execute("SELECT * FROM moon_cake_resource_records WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        return MoonCakeResourceRecord(row['key'], row['subject'], row['state'], row['version'], row['actor'], row['effective_at'], json.loads(row['payload']))

    def list(self, state: str | None = None) -> list[MoonCakeResourceRecord]:
        if state is None:
            rows = self.db.execute("SELECT * FROM moon_cake_resource_records ORDER BY effective_at,key").fetchall()
        else:
            rows = self.db.execute("SELECT * FROM moon_cake_resource_records WHERE state=? ORDER BY effective_at,key", (state,)).fetchall()
        return [MoonCakeResourceRecord(r['key'], r['subject'], r['state'], r['version'], r['actor'], r['effective_at'], json.loads(r['payload'])) for r in rows]

    def apply(self, key: str, subject: str, state: str, payload: dict[str, Any], actor: str, request_id: str, effective_at: str) -> MoonCakeResourceRecord:
        if not key or not subject or not actor or not request_id:
            raise MoonCakeResourceError('key、subject、actor 和 request_id 不能为空')
        if not state or len(state) > 40:
            raise MoonCakeResourceError('状态无效')
        if not isinstance(payload, dict):
            raise MoonCakeResourceError('payload 必须是对象')
        now = self._now()
        with self.db:
            duplicate = self.db.execute("SELECT after_state FROM moon_cake_resource_events WHERE key=? AND request_id=?", (key, request_id)).fetchone()
            if duplicate:
                found = self.get(key)
                if found is None:
                    raise MoonCakeResourceError('幂等事件缺少记录')
                return found
            old = self.get(key)
            version = 1 if old is None else old.version + 1
            before = None if old is None else old.state
            self.db.execute("INSERT INTO moon_cake_resource_records(key,subject,state,version,actor,effective_at,payload,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET subject=excluded.subject,state=excluded.state,version=excluded.version,actor=excluded.actor,effective_at=excluded.effective_at,payload=excluded.payload,updated_at=excluded.updated_at", (key, subject, state, version, actor, effective_at, json.dumps(payload, ensure_ascii=False, sort_keys=True), now))
            self.db.execute("INSERT INTO moon_cake_resource_events(key,action,request_id,actor,before_state,after_state,detail,created_at) VALUES(?,?,?,?,?,?,?,?)", (key, 'apply', request_id, actor, before, state, json.dumps(payload, ensure_ascii=False, sort_keys=True), now))
        result = self.get(key)
        if result is None:
            raise MoonCakeResourceError('保存后无法读取记录')
        return result

    def history(self, key: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT id,key,action,request_id,actor,before_state,after_state,detail,created_at FROM moon_cake_resource_events WHERE key=? ORDER BY id", (key,)).fetchall()
        return [dict(r) for r in rows]

    def reconcile(self, keys: Iterable[str]) -> dict[str, Any]:
        report = {'checked': 0, 'valid': 0, 'issues': []}
        for key in keys:
            report['checked'] += 1
            record = self.get(key)
            events = self.history(key)
            if record is None or not events:
                report['issues'].append({'key': key, 'reason': '缺少记录或事件'})
                continue
            if record.version != len(events):
                report['issues'].append({'key': key, 'reason': '版本与事件数量不一致'})
                continue
            report['valid'] += 1
        return report

def validate_resource(record: MoonCakeResourceRecord) -> list[str]:
    errors: list[str] = []
    if record.version < 1:
        errors.append('版本必须为正数')
    if not record.effective_at:
        errors.append('必须提供生效时间')
    if record.state in {'approved', 'published'} and not record.payload:
        errors.append('生效状态必须带有业务载荷')
    if len(record.subject.strip()) < 2:
        errors.append('主体名称过短')
    return errors

def summarize_resource(records: Iterable[MoonCakeResourceRecord]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in records:
        result[item.state] = result.get(item.state, 0) + 1
    return result

