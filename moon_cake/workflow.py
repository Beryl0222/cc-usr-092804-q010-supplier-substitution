"""跨模块事务编排。"""
from .ledger import LedgerStore
from .audit import AuditStore
from .report import summarize_report
class Workflow:
    def __init__(self, db):
        self.ledger = LedgerStore(db); self.audit = AuditStore(db); self.db = db
    def apply(self, key, subject, state, payload, actor, request_id, effective_at):
        record = self.ledger.apply(key, subject, state, payload, actor, request_id, effective_at)
        self.audit.apply(key, key, state, payload, actor, request_id, effective_at)
        return record
    def show(self, key):
        record = self.ledger.get(key)
        return {'record': record, 'history': self.ledger.history(key), 'audit': self.audit.history(key)}
    def summary(self):
        return summarize_report(self.ledger.list())
