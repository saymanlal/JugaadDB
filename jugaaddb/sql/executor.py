from typing import Any

from .ast import (
    BinaryExpression,
    Identifier,
    Literal,
    LogicalExpression,
)
from .errors import SQLExecutionError
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
from .result import CommandResult, QueryResult
from ..indexing.scan import IndexScan as IndexScanner


class Executor:
    def __init__(self, database):
        self.database = database

    def execute(self, plan):
        if not isinstance(
            plan,
            (
                Projection,
                InsertPlan,
                UpdatePlan,
                DeletePlan,
                CreateTablePlan,
                CreateIndexPlan,
            ),
        ):
            raise TypeError(
                f"Unsupported execution plan: "
                f"{type(plan).__name__}"
            )

        try:
            if isinstance(plan, Projection):
                return self._execute_select(plan)

            if isinstance(plan, InsertPlan):
                return self._execute_insert(plan)

            if isinstance(plan, UpdatePlan):
                return self._execute_update(plan)

            if isinstance(plan, DeletePlan):
                return self._execute_delete(plan)

            if isinstance(plan, CreateTablePlan):
                return self._execute_create_table(plan)

            if isinstance(plan, CreateIndexPlan):
                return self._execute_create_index(plan)

        except SQLExecutionError:
            raise

        except (ValueError, TypeError) as error:
            raise SQLExecutionError(
                str(error)
            ) from error

    def _execute_select(self, plan):
        table = self._get_table(plan.source)

        self._validate_expression_if_present(
            plan.source,
            table,
        )

        rows = self._execute_source(plan.source)

        available_columns = {
            column.name
            for column in table.schema.columns
        }

        if plan.columns == (Identifier("*"),):
            columns = tuple(
                column.name
                for column in table.schema.columns
            )

            result_rows = [
                row.copy()
                for row in rows
            ]

        else:
            columns = tuple(
                column.name
                for column in plan.columns
            )

            if len(columns) != len(set(columns)):
                raise SQLExecutionError(
                    "Duplicate columns are not allowed in SELECT."
                )

            self._validate_columns_exist(
                columns,
                available_columns,
            )

            result_rows = [
                {
                    column: row[column]
                    for column in columns
                }
                for row in rows
            ]

        return QueryResult(
            columns=columns,
            rows=tuple(result_rows),
            query_type="SELECT",
        )

    def _execute_source(self, source):
        if isinstance(source, TableScan):
            table = self.database.table(
                source.table.name
            )

            return table.select_all()

        if isinstance(source, IndexScan):
            rows = self._execute_planned_index_scan(
                source
            )

            if source.condition is None:
                return rows

            return [
                row
                for row in rows
                if self._evaluate(
                    source.condition,
                    row,
                )
            ]

        if isinstance(source, Filter):
            table = self._get_table(
                source.source
            )

            self._validate_expression_columns(
                source.condition,
                table,
            )

            indexed_rows = self._execute_index_scan(
                source.condition,
                table,
            )

            if indexed_rows is not None:
                return [
                    row
                    for row in indexed_rows
                    if self._evaluate(
                        source.condition,
                        row,
                    )
                ]

            rows = self._execute_source(
                source.source
            )

            return [
                row
                for row in rows
                if self._evaluate(
                    source.condition,
                    row,
                )
            ]

        raise SQLExecutionError(
            f"Unsupported execution source: "
            f"{type(source).__name__}"
        )

    def _execute_planned_index_scan(
        self,
        plan,
    ):
        table = self.database.table(
            plan.table.name
        )

        available_columns = {
            column.name
            for column in table.schema.columns
        }

        self._validate_columns_exist(
            [plan.column.name],
            available_columns,
        )

        indexes = (
            self.database.index_manager
            .indexes_for_column(
                table.name,
                plan.column.name,
            )
        )

        index = next(
            (
                candidate
                for candidate in indexes
                if candidate.name == plan.index.name
            ),
            None,
        )

        if index is None:
            raise SQLExecutionError(
                f"Index does not exist: {plan.index.name}"
            )

        record_ids = IndexScanner(
            index
        ).exact(
            plan.value
        )

        rows = []

        for record_id in record_ids:
            try:
                row = table.row_by_record_id(
                    record_id
                )
            except ValueError as error:
                raise SQLExecutionError(
                    str(error)
                ) from error

            rows.append(row)

        return rows

    def _execute_index_scan(
        self,
        condition,
        table,
    ):
        parsed = self._extract_indexable_equality(
            condition
        )

        if parsed is None:
            return None

        column, value = parsed

        indexes = (
            self.database.index_manager
            .indexes_for_column(
                table.name,
                column,
            )
        )

        if not indexes:
            return None

        index = indexes[0]
        scan = IndexScanner(index)

        record_ids = scan.exact(value)

        rows = []

        for record_id in record_ids:
            try:
                row = table.row_by_record_id(
                    record_id
                )
            except ValueError as error:
                raise SQLExecutionError(
                    str(error)
                ) from error

            rows.append(row)

        return rows

    def _extract_indexable_equality(
        self,
        condition,
    ):
        if not isinstance(
            condition,
            BinaryExpression,
        ):
            return None

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

    def _execute_insert(self, plan):
        table = self.database.table(
            plan.table.name
        )

        column_names = tuple(
            column.name
            for column in plan.columns
        )

        if len(column_names) != len(plan.values):
            raise SQLExecutionError(
                "INSERT column count does not match value count."
            )

        if len(column_names) != len(
            set(column_names)
        ):
            raise SQLExecutionError(
                "Duplicate columns are not allowed in INSERT."
            )

        available_columns = {
            column.name
            for column in table.schema.columns
        }

        self._validate_columns_exist(
            column_names,
            available_columns,
        )

        row = {
            column.name: value.value
            for column, value in zip(
                plan.columns,
                plan.values,
            )
        }

        table.insert(row)

        return CommandResult(
            affected_rows=1,
            query_type="INSERT",
        )

    def _execute_update(self, plan):
        table = self._get_table(
            plan.source
        )

        available_columns = {
            column.name
            for column in table.schema.columns
        }

        assignment_names = tuple(
            assignment.column.name
            for assignment in plan.assignments
        )

        if not assignment_names:
            raise SQLExecutionError(
                "UPDATE requires at least one assignment."
            )

        if len(assignment_names) != len(
            set(assignment_names)
        ):
            raise SQLExecutionError(
                "Duplicate columns are not allowed in UPDATE."
            )

        self._validate_columns_exist(
            assignment_names,
            available_columns,
        )

        self._validate_update_delete_condition(
            plan.source
        )

        self._validate_expression_if_present(
            plan.source,
            table,
        )

        rows = self._execute_source(
            plan.source
        )

        changes = {
            assignment.column.name:
            assignment.value.value
            for assignment in plan.assignments
        }

        if not rows:
            return CommandResult(
                affected_rows=0,
                query_type="UPDATE",
            )

        primary_key = self._primary_key_column(
            table
        )

        count = 0

        for row in rows:
            condition = {
                primary_key: row[primary_key]
            }

            count += table.update(
                condition,
                changes,
            )

        return CommandResult(
            affected_rows=count,
            query_type="UPDATE",
        )

    def _execute_delete(self, plan):
        table = self._get_table(
            plan.source
        )

        self._validate_update_delete_condition(
            plan.source
        )

        self._validate_expression_if_present(
            plan.source,
            table,
        )

        rows = self._execute_source(
            plan.source
        )

        if not rows:
            return CommandResult(
                affected_rows=0,
                query_type="DELETE",
            )

        primary_key = self._primary_key_column(
            table
        )

        count = 0

        for row in rows:
            condition = {
                primary_key: row[primary_key]
            }

            count += table.delete(
                condition
            )

        return CommandResult(
            affected_rows=count,
            query_type="DELETE",
        )

    def _execute_create_table(self, plan):
        from ..core.schema import Column

        columns = [
            Column(
                name=column.name.name,
                data_type=column.data_type.name,
                primary_key=column.primary_key,
                nullable=column.nullable,
                unique=column.unique,
            )
            for column in plan.columns
        ]

        self.database.create_table(
            plan.table.name,
            columns,
        )

        return CommandResult(
            affected_rows=1,
            query_type="CREATE TABLE",
        )

    def _execute_create_index(self, plan):
        table = self.database.table(
            plan.table.name
        )

        available_columns = {
            column.name
            for column in table.schema.columns
        }

        self._validate_columns_exist(
            [plan.column.name],
            available_columns,
        )

        if self.database.index_manager.indexes_for_column(
            plan.table.name,
            plan.column.name,
        ):
            raise SQLExecutionError(
                f"An index already exists for column: "
                f"{plan.column.name}"
            )

        index = self.database.index_manager.create_index(
            table_name=plan.table.name,
            index_name=plan.index.name,
            column=plan.column.name,
            index_type="btree",
        )

        for record_id, row in table.select_all_with_ids():
            value = row.get(
                plan.column.name
            )

            if value is None:
                continue

            index.insert(
                value,
                record_id,
            )

        return CommandResult(
            affected_rows=1,
            query_type="CREATE INDEX",
        )

    def _evaluate(
        self,
        expression,
        row: dict[str, Any],
    ) -> bool:
        if isinstance(
            expression,
            BinaryExpression,
        ):
            left = self._value(
                expression.left,
                row,
            )

            right = self._value(
                expression.right,
                row,
            )

            return self._compare(
                left,
                expression.operator,
                right,
            )

        if isinstance(
            expression,
            LogicalExpression,
        ):
            if expression.operator == "AND":
                return (
                    self._evaluate(
                        expression.left,
                        row,
                    )
                    and
                    self._evaluate(
                        expression.right,
                        row,
                    )
                )

            if expression.operator == "OR":
                return (
                    self._evaluate(
                        expression.left,
                        row,
                    )
                    or
                    self._evaluate(
                        expression.right,
                        row,
                    )
                )

            raise SQLExecutionError(
                f"Unsupported logical operator: "
                f"{expression.operator}"
            )

        raise SQLExecutionError(
            f"Unsupported expression: "
            f"{type(expression).__name__}"
        )

    def _value(
        self,
        expression,
        row,
    ):
        if isinstance(
            expression,
            Identifier,
        ):
            if expression.name not in row:
                raise SQLExecutionError(
                    f"Unknown column: "
                    f"{expression.name}"
                )

            return row[expression.name]

        if isinstance(
            expression,
            Literal,
        ):
            return expression.value

        raise SQLExecutionError(
            f"Unsupported expression value: "
            f"{type(expression).__name__}"
        )

    def _compare(
        self,
        left,
        operator,
        right,
    ):
        if left is None or right is None:
            if operator == "!=":
                return (
                    left is not None
                    or right is not None
                )

            return False

        if operator == "=":
            return left == right

        if operator == "!=":
            return left != right

        if operator == "<":
            return left < right

        if operator == "<=":
            return left <= right

        if operator == ">":
            return left > right

        if operator == ">=":
            return left >= right

        raise SQLExecutionError(
            f"Unsupported comparison operator: "
            f"{operator}"
        )

    def _get_table(self, source):
        while isinstance(
            source,
            Filter,
        ):
            source = source.source

        if isinstance(
            source,
            TableScan,
        ):
            return self.database.table(
                source.table.name
            )

        if isinstance(
            source,
            IndexScan,
        ):
            return self.database.table(
                source.table.name
            )

        raise SQLExecutionError(
            f"Cannot determine table from: "
            f"{type(source).__name__}"
        )

    def _primary_key_column(self, table):
        for column in table.schema.columns:
            if column.primary_key:
                return column.name

        raise SQLExecutionError(
            "UPDATE and DELETE require a primary key."
        )

    def _validate_columns_exist(
        self,
        columns,
        available_columns,
    ):
        for column in columns:
            if column not in available_columns:
                raise SQLExecutionError(
                    f"Unknown column: {column}"
                )

    def _validate_expression_if_present(
        self,
        source,
        table,
    ):
        if isinstance(
            source,
            Filter,
        ):
            self._validate_expression_columns(
                source.condition,
                table,
            )

        elif isinstance(
            source,
            IndexScan,
        ):
            if source.condition is not None:
                self._validate_expression_columns(
                    source.condition,
                    table,
                )

    def _validate_expression_columns(
        self,
        expression,
        table,
    ):
        available_columns = {
            column.name
            for column in table.schema.columns
        }

        if isinstance(
            expression,
            BinaryExpression,
        ):
            self._validate_expression_value(
                expression.left,
                available_columns,
            )

            self._validate_expression_value(
                expression.right,
                available_columns,
            )

            return

        if isinstance(
            expression,
            LogicalExpression,
        ):
            self._validate_expression_columns(
                expression.left,
                table,
            )

            self._validate_expression_columns(
                expression.right,
                table,
            )

            return

        raise SQLExecutionError(
            f"Unsupported expression: "
            f"{type(expression).__name__}"
        )

    def _validate_expression_value(
        self,
        expression,
        available_columns,
    ):
        if isinstance(
            expression,
            Identifier,
        ):
            if expression.name not in available_columns:
                raise SQLExecutionError(
                    f"Unknown column: "
                    f"{expression.name}"
                )

            return

        if isinstance(
            expression,
            Literal,
        ):
            return

        raise SQLExecutionError(
            f"Unsupported expression value: "
            f"{type(expression).__name__}"
        )

    def _validate_update_delete_condition(
        self,
        source,
    ):
        if isinstance(
            source,
            IndexScan,
        ):
            return

        if not isinstance(
            source,
            Filter,
        ):
            return

        condition = source.condition

        if isinstance(
            condition,
            LogicalExpression,
        ):
            self._validate_update_delete_logical_condition(
                condition
            )
            return

        if not isinstance(
            condition,
            BinaryExpression,
        ):
            raise SQLExecutionError(
                "UPDATE and DELETE currently require "
                "a valid condition."
            )

        if condition.operator != "=":
            raise SQLExecutionError(
                "UPDATE and DELETE currently support "
                "only equality conditions."
            )

        if not isinstance(
            condition.left,
            Identifier,
        ):
            raise SQLExecutionError(
                "Condition must compare a column."
            )

        if not isinstance(
            condition.right,
            Literal,
        ):
            raise SQLExecutionError(
                "Condition value must be a literal."
            )

    def _validate_update_delete_logical_condition(
        self,
        condition,
    ):
        if not isinstance(
            condition,
            LogicalExpression,
        ):
            raise SQLExecutionError(
                "Invalid UPDATE or DELETE condition."
            )

        self._validate_update_delete_condition_expression(
            condition.left
        )

        self._validate_update_delete_condition_expression(
            condition.right
        )

    def _validate_update_delete_condition_expression(
        self,
        expression,
    ):
        if isinstance(
            expression,
            LogicalExpression,
        ):
            self._validate_update_delete_logical_condition(
                expression
            )
            return

        if not isinstance(
            expression,
            BinaryExpression,
        ):
            raise SQLExecutionError(
                "Invalid UPDATE or DELETE condition."
            )

        if expression.operator not in {
            "=",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
        }:
            raise SQLExecutionError(
                "Unsupported UPDATE or DELETE condition operator."
            )

        if not isinstance(
            expression.left,
            Identifier,
        ):
            raise SQLExecutionError(
                "Condition must compare a column."
            )

        if not isinstance(
            expression.right,
            Literal,
        ):
            raise SQLExecutionError(
                "Condition value must be a literal."
            )