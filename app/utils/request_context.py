from contextvars import ContextVar
from typing import Optional, Dict
import uuid

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_workflow_id: ContextVar[Optional[str]] = ContextVar("workflow_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def new_request_id() -> str:
    return str(uuid.uuid4())


def new_workflow_id() -> str:
    return str(uuid.uuid4())


def set_request_id(request_id: Optional[str]) -> None:
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_workflow_id(workflow_id: Optional[str]) -> None:
    _workflow_id.set(workflow_id)


def get_workflow_id() -> Optional[str]:
    return _workflow_id.get()


def set_user_id(user_id: Optional[str]) -> None:
    _user_id.set(user_id)


def get_user_id() -> Optional[str]:
    return _user_id.get()


def clear_context() -> None:
    set_request_id(None)
    set_workflow_id(None)
    set_user_id(None)


def context_snapshot() -> Dict[str, Optional[str]]:
    return {
        "request_id": get_request_id(),
        "workflow_id": get_workflow_id(),
        "user_id": get_user_id(),
    }
