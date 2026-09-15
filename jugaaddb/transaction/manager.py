from dataclasses import dataclass
from enum import Enum


class TransactionState(str, Enum):
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


@dataclass
class Transaction:
    transaction_id: int
    state: TransactionState = TransactionState.ACTIVE


class TransactionManager:
    def __init__(self):
        self._next_transaction_id = 1
        self._transactions: dict[int, Transaction] = {}

    def begin(self) -> Transaction:
        transaction_id = self._next_transaction_id
        self._next_transaction_id += 1

        transaction = Transaction(
            transaction_id=transaction_id,
            state=TransactionState.ACTIVE,
        )

        self._transactions[transaction_id] = transaction

        return transaction

    def commit(
        self,
        transaction_id: int,
    ) -> Transaction:
        transaction = self._get_transaction(
            transaction_id
        )

        if transaction.state is not TransactionState.ACTIVE:
            raise ValueError(
                f"Transaction is not active: {transaction_id}"
            )

        transaction.state = TransactionState.COMMITTED

        return transaction

    def rollback(
        self,
        transaction_id: int,
    ) -> Transaction:
        transaction = self._get_transaction(
            transaction_id
        )

        if transaction.state is not TransactionState.ACTIVE:
            raise ValueError(
                f"Transaction is not active: {transaction_id}"
            )

        transaction.state = TransactionState.ABORTED

        return transaction

    def get(
        self,
        transaction_id: int,
    ) -> Transaction:
        return self._get_transaction(
            transaction_id
        )

    def exists(
        self,
        transaction_id: int,
    ) -> bool:
        return transaction_id in self._transactions

    def active_transactions(
        self,
    ) -> list[Transaction]:
        return [
            transaction
            for transaction in self._transactions.values()
            if transaction.state is TransactionState.ACTIVE
        ]

    def committed_transactions(
        self,
    ) -> list[Transaction]:
        return [
            transaction
            for transaction in self._transactions.values()
            if transaction.state is TransactionState.COMMITTED
        ]

    def aborted_transactions(
        self,
    ) -> list[Transaction]:
        return [
            transaction
            for transaction in self._transactions.values()
            if transaction.state is TransactionState.ABORTED
        ]

    def _get_transaction(
        self,
        transaction_id: int,
    ) -> Transaction:
        if type(transaction_id) is not int:
            raise TypeError(
                "Transaction ID must be an integer."
            )

        if transaction_id <= 0:
            raise ValueError(
                "Transaction ID must be greater than zero."
            )

        transaction = self._transactions.get(
            transaction_id
        )

        if transaction is None:
            raise ValueError(
                f"Transaction does not exist: {transaction_id}"
            )

        return transaction