class DatabaseRouter:
    """
    Database router controlling table access between:
    - 'default': SQLite for Django auth, sessions, RBAC, report notes, and logs.
    - 'adventureworks': Microsoft SQL Server read-only analytical database.
    """
    sqlite_apps = {'auth', 'contenttypes', 'sessions', 'admin', 'messages', 'accounts', 'governance'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.sqlite_apps:
            return 'default'
        return 'adventureworks'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.sqlite_apps:
            return 'default'
        # Prevent any writes to AdventureWorks to keep it strictly read-only
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.sqlite_apps and
            obj2._meta.app_label in self.sqlite_apps
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.sqlite_apps:
            return db == 'default'
        # No migrations on AdventureWorks
        return False
