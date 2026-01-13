from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Account,
    Artifact,
    AuditLog,
    Bant,
    Base,
    Contact,
    Email,
    Pipeline,
    Task,
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def test_crud_models(session: Session) -> None:
    account = Account(name="Inscalia", industry="Retail")
    session.add(account)
    session.flush()

    contact = Contact(
        account_id=account.id,
        first_name="Ada",
        last_name="Lovelace",
        title="CTO",
    )
    session.add(contact)
    session.flush()

    email = Email(contact_id=contact.id, address="ada@example.com", version=1)
    session.add(email)

    pipeline = Pipeline(account_id=account.id, name="Enterprise Deal", stage="Discovery", amount_cents=250000)
    session.add(pipeline)
    session.flush()

    bant = Bant(
        pipeline_id=pipeline.id,
        budget="Approved",
        authority="CFO",
        need="Modernize stack",
        timeline="Q3",
    )
    session.add(bant)

    task = Task(account_id=account.id, contact_id=contact.id, title="Follow up", status="open")
    session.add(task)
    session.flush()

    artifact = Artifact(task_id=task.id, name="Proposal", uri="s3://artifacts/proposal.pdf")
    session.add(artifact)

    audit_log = AuditLog(
        trigger_source="unit-test",
        input_json='{"key": "value"}',
        output_result='{"result": "ok"}',
    )
    session.add(audit_log)
    session.commit()

    account.name = "Inscalia Updated"
    session.commit()

    session.delete(artifact)
    session.commit()

    refreshed = session.get(Account, account.id)
    assert refreshed is not None
    assert refreshed.name == "Inscalia Updated"
    assert session.query(Artifact).count() == 0
    assert session.query(AuditLog).count() == 1


def test_email_versions_are_immutable(session: Session) -> None:
    account = Account(name="Immutable Corp")
    session.add(account)
    session.flush()
    contact = Contact(account_id=account.id, first_name="Linus", last_name="Torvalds")
    session.add(contact)
    session.flush()
    email = Email(contact_id=contact.id, address="linus@example.com", version=1)
    session.add(email)
    session.commit()

    email.address = "new@example.com"
    with pytest.raises(ValueError, match="immutable"):
        session.commit()
    session.rollback()


def test_constraints_enforced(session: Session) -> None:
    contact = Contact(account_id=1, first_name="Missing", last_name="Account")
    session.add(contact)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    account = Account(name="Valid Account")
    session.add(account)
    session.flush()
    contact = Contact(account_id=account.id, first_name="Valid", last_name="Contact")
    session.add(contact)
    session.flush()

    email_v1 = Email(contact_id=contact.id, address="valid@example.com", version=1)
    session.add(email_v1)
    session.commit()

    duplicate_version = Email(contact_id=contact.id, address="other@example.com", version=1)
    session.add(duplicate_version)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    bad_email = Email(contact_id=9999, address="missing@example.com", version=2)
    session.add(bad_email)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
