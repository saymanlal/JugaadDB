from .ast import (
    CreateTableStatement,
    DeleteStatement,
    InsertStatement,
    SelectStatement,
    UpdateStatement,
)
from .plan import (
    CreateTablePlan,
    DeletePlan,
    Filter,
    InsertPlan,
    Projection,
    TableScan,
    UpdatePlan,
)


class Planner:
    def plan(self, statement):
        if isinstance(statement, SelectStatement):
            return self._plan_select(statement)

        if isinstance(statement, InsertStatement):
            return self._plan_insert(statement)

        if isinstance(statement, UpdateStatement):
            return self._plan_update(statement)

        if isinstance(statement, DeleteStatement):
            return self._plan_delete(statement)

        if isinstance(statement, CreateTableStatement):
            return self._plan_create_table(statement)

        raise TypeError(
            f"Unsupported AST node: {type(statement).__name__}"
        )

    def _plan_select(self, statement):
        source = TableScan(statement.table)

        if statement.where is not None:
            source = Filter(
                source=source,
                condition=statement.where,
            )

        return Projection(
            source=source,
            columns=statement.columns,
        )

    def _plan_insert(self, statement):
        return InsertPlan(
            table=statement.table,
            columns=statement.columns,
            values=statement.values,
        )

    def _plan_update(self, statement):
        source = TableScan(statement.table)

        if statement.where is not None:
            source = Filter(
                source=source,
                condition=statement.where,
            )

        return UpdatePlan(
            source=source,
            assignments=statement.assignments,
        )

    def _plan_delete(self, statement):
        source = TableScan(statement.table)

        if statement.where is not None:
            source = Filter(
                source=source,
                condition=statement.where,
            )

        return DeletePlan(source=source)

    def _plan_create_table(self, statement):
        return CreateTablePlan(
            table=statement.table,
            columns=statement.columns,
        )