"""Seed default users and built-in tests (T022).

Creates one ADMIN and one REVIEWER, registers the six Python quality METRIC
tests with default weights, plus at least one AI_AGENT test (the AI-agent plugin
lands in US5; the Test row is seeded so the configured set satisfies FR-013).
"""
from __future__ import annotations

from src.api.auth_deps import hash_password
from src.db import SessionLocal, init_db
from src.models import Role, Test, TestType, User
from src.tests_plugins.quality.builtin import QUALITY_PLUGINS


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(
                User(username="admin", password_hash=hash_password("admin"), role=Role.ADMIN)
            )
        if not db.query(User).filter(User.username == "reviewer").first():
            db.add(
                User(
                    username="reviewer",
                    password_hash=hash_password("reviewer"),
                    role=Role.REVIEWER,
                )
            )
        for key, name, _factory in QUALITY_PLUGINS:
            if not db.query(Test).filter(Test.key == key).first():
                db.add(
                    Test(
                        key=key,
                        name=name,
                        type=TestType.METRIC,
                        enabled=True,
                        default_weight=1.0,
                    )
                )
        if not db.query(Test).filter(Test.key == "ai.readability").first():
            db.add(
                Test(
                    key="ai.readability",
                    name="AI Readability Review",
                    type=TestType.AI_AGENT,
                    theme="readability",
                    enabled=False,  # enabled once the US5 plugin is implemented
                    default_weight=1.0,
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
