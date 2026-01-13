from __future__ import annotations

from typing import Any

from audit_log import get_default_audit_log_store


def append_audit_log(
    trigger_source: str,
    input_payload: dict[str, Any],
    output_result: dict[str, Any],
) -> None:
    store = get_default_audit_log_store()
    store.append(trigger_source, input_payload, output_result)
