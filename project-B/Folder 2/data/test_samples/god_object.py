# Expected Smells:
# - god_object (MEDIUM)
# - too_many_parameters (LOW)

"""God object sample with too many responsibilities."""


class ApplicationManager:
    """Single class intentionally handling DB, logging, and caching responsibilities."""

    def __init__(self):
        self.cache_enabled = True
        self.log_target = "stdout"
        self.db_dsn = "sqlite:///demo.db"

    def db_connect(self):
        return f"connect:{self.db_dsn}"

    def db_query(self, sql):
        return f"query:{sql}"

    def db_insert(self, row):
        return f"insert:{row}"

    def cache_get(self, key):
        return f"cache_get:{key}"

    def cache_set(self, key, value):
        return f"cache_set:{key}:{value}"

    def cache_clear(self):
        return "cache_clear"

    def log_info(self, message):
        return f"info:{message}"

    def log_warn(self, message):
        return f"warn:{message}"

    def log_error(self, message):
        return f"error:{message}"

    def configure_all(self, db_host, db_port, db_name, db_user, db_password, log_level):
        return f"{db_host}:{db_port}:{db_name}:{db_user}:{db_password}:{log_level}"
