import os


def getenv_boolean(var_name, default_value=False):
    result = default_value
    env_value = os.getenv(var_name)
    if env_value is not None:
        result = env_value.upper() in ("TRUE", "1")
    return result


POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "kac")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "kac")
POSTGRES_DB = os.getenv("POSTGRES_DB", "kac")


SECRET_KEY = os.getenvb(b"SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = os.urandom(32)


EVENT_ID = os.getenv("EVENT_ID")

if not EVENT_ID:
    raise RuntimeError("Please specify EVENT_ID")


MAX_TXN_DURATION = 10
