from contextvars import ContextVar

_default_current_user = {"usr_id": "TEST-USR-ID"}
current_user = ContextVar("current_user", default=_default_current_user)

transaction_id_var = ContextVar("transaction_id", default=None)
