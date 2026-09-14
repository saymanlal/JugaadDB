from .ast import (
    BinaryExpression,
    CreateIndexStatement,
    CreateTableStatement,
    DeleteStatement,
    Identifier,
    InsertStatement,
    Literal,
    LogicalExpression,
    SelectStatement,
    UpdateStatement,
)
from .plan import (
    CreateIndexPlan,
    CreateTablePlan,
    DeletePlan,
    Filter,
    IndexScan,
    InsertPlan,
    Projection,
    TableScan,
    UpdatePlan,
)


class Planner:
    def __init__(self, database=None):
        self.database = database

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

        if isinstance(statement, CreateIndexStatement):
            return self._plan_create_index(statement)

        raise TypeError(
            f"Unsupported AST node: {type(statement).__name__}"
        )

    def _plan_select(self, statement):
        source = self._plan_filtered_source(
            statement.table,
            statement.where,
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
        source = self._plan_filtered_source(
            statement.table,
            statement.where,
        )

        return UpdatePlan(
            source=source,
            assignments=statement.assignments,
        )

    def _plan_delete(self, statement):
        source = self._plan_filtered_source(
            statement.table,
            statement.where,
        )

        return DeletePlan(
            source=source,
        )

    def _plan_create_table(self, statement):
        return CreateTablePlan(
            table=statement.table,
            columns=statement.columns,
        )

    def _plan_create_index(self, statement):
        return CreateIndexPlan(
            index=statement.index,
            table=statement.table,
            column=statement.column,
        )

    def _plan_filtered_source(
        self,
        table,
        condition,
    ):
        if condition is None:
            return TableScan(table)

        index_scan = self._try_index_scan(
            table,
            condition,
        )

        if index_scan is not None:
            return index_scan

        return Filter(
            source=TableScan(table),
            condition=condition,
        )

    def _try_index_scan(
        self,
        table,
        condition,
    ):
        if self.database is None:
            return None

        predicates = self._extract_indexable_predicates(
            condition
        )

        if not predicates:
            return None

        candidates = []

        for predicate in predicates:
            column_name, value = predicate

            indexes = (
                self.database.index_manager
                .indexes_for_column(
                    table.name,
                    column_name,
                )
            )

            for index in indexes:
                candidates.append(
                    (
                        self._index_score(index),
                        index.name,
                        index,
                        column_name,
                        value,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda candidate: (
                -candidate[0],
                candidate[1],
            )
        )

        _, _, index, column_name, value = candidates[0]

        return IndexScan(
            table=table,
            index=Identifier(index.name),
            column=Identifier(column_name),
            value=value,
            condition=condition,
        )

    def _extract_indexable_predicates(
        self,
        condition,
    ):
        if isinstance(
            condition,
            BinaryExpression,
        ):
            predicate = self._extract_equality_predicate(
                condition
            )

            if predicate is None:
                return []

            return [predicate]

        if isinstance(
            condition,
            LogicalExpression,
        ):
            if condition.operator != "AND":
                return []

            return (
                self._extract_indexable_predicates(
                    condition.left
                )
                +
                self._extract_indexable_predicates(
                    condition.right
                )
            )

        return []

    def _extract_equality_predicate(
        self,
        condition,
    ):
        if condition.operator != "=":
            return None

        if not isinstance(
            condition.left,
            Identifier,
        ):
            return None

        if not isinstance(
            condition.right,
            Literal,
        ):
            return None

        return (
            condition.left.name,
            condition.right.value,
        )

    def _index_score(self, index):
        index_type = getattr(
            index,
            "index_type",
            None,
        )

        if index_type == "btree":
            return 100

        return 10