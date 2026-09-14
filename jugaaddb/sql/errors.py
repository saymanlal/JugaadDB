class SQLError(Exception):
    pass


class SQLSyntaxError(SQLError, SyntaxError):
    pass


class SQLExecutionError(SQLError, ValueError):
    pass


class SQLPlanningError(SQLError, TypeError):
    pass