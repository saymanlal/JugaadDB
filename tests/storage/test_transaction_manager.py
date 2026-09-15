import pytest

from jugaaddb.transaction import (
    TransactionManager,
    TransactionState,
)


def test_begin_creates_active_transaction():
    manager = TransactionManager()

    transaction = manager.begin()

    assert transaction.transaction_id == 1
    assert transaction.state is TransactionState.ACTIVE


def test_transaction_ids_are_monotonic():
    manager = TransactionManager()

    first = manager.begin()
    second = manager.begin()
    third = manager.begin()

    assert first.transaction_id == 1
    assert second.transaction_id == 2
    assert third.transaction_id == 3


def test_commit_changes_transaction_state():
    manager = TransactionManager()

    transaction = manager.begin()

    committed = manager.commit(
        transaction.transaction_id
    )

    assert committed.state is TransactionState.COMMITTED
    assert manager.get(
        transaction.transaction_id
    ).state is TransactionState.COMMITTED


def test_rollback_changes_transaction_state():
    manager = TransactionManager()

    transaction = manager.begin()

    aborted = manager.rollback(
        transaction.transaction_id
    )

    assert aborted.state is TransactionState.ABORTED
    assert manager.get(
        transaction.transaction_id
    ).state is TransactionState.ABORTED


def test_committed_transaction_cannot_commit_again():
    manager = TransactionManager()

    transaction = manager.begin()

    manager.commit(
        transaction.transaction_id
    )

    with pytest.raises(ValueError):
        manager.commit(
            transaction.transaction_id
        )


def test_committed_transaction_cannot_rollback():
    manager = TransactionManager()

    transaction = manager.begin()

    manager.commit(
        transaction.transaction_id
    )

    with pytest.raises(ValueError):
        manager.rollback(
            transaction.transaction_id
        )


def test_aborted_transaction_cannot_commit():
    manager = TransactionManager()

    transaction = manager.begin()

    manager.rollback(
        transaction.transaction_id
    )

    with pytest.raises(ValueError):
        manager.commit(
            transaction.transaction_id
        )


def test_aborted_transaction_cannot_rollback_again():
    manager = TransactionManager()

    transaction = manager.begin()

    manager.rollback(
        transaction.transaction_id
    )

    with pytest.raises(ValueError):
        manager.rollback(
            transaction.transaction_id
        )


def test_get_returns_existing_transaction():
    manager = TransactionManager()

    transaction = manager.begin()

    result = manager.get(
        transaction.transaction_id
    )

    assert result is transaction


def test_exists_identifies_existing_transaction():
    manager = TransactionManager()

    transaction = manager.begin()

    assert manager.exists(
        transaction.transaction_id
    )

    assert not manager.exists(999)


def test_active_transactions_returns_only_active():
    manager = TransactionManager()

    first = manager.begin()
    second = manager.begin()
    third = manager.begin()

    manager.commit(
        second.transaction_id
    )

    manager.rollback(
        third.transaction_id
    )

    active = manager.active_transactions()

    assert active == [first]


def test_committed_transactions_returns_only_committed():
    manager = TransactionManager()

    first = manager.begin()
    second = manager.begin()

    manager.commit(
        second.transaction_id
    )

    assert manager.committed_transactions() == [
        second
    ]


def test_aborted_transactions_returns_only_aborted():
    manager = TransactionManager()

    first = manager.begin()
    second = manager.begin()

    manager.rollback(
        first.transaction_id
    )

    assert manager.aborted_transactions() == [
        first
    ]

    assert second.state is TransactionState.ACTIVE


@pytest.mark.parametrize(
    "transaction_id",
    [0, -1, True, 1.5, "1", None],
)
def test_invalid_transaction_id_is_rejected(
    transaction_id,
):
    manager = TransactionManager()

    with pytest.raises(
        TypeError if type(transaction_id) is not int
        else ValueError
    ):
        manager.get(transaction_id)


@pytest.mark.parametrize(
    "transaction_id",
    [999, 1000],
)
def test_unknown_transaction_id_is_rejected(
    transaction_id,
):
    manager = TransactionManager()

    with pytest.raises(ValueError):
        manager.get(transaction_id)


def test_manager_can_handle_many_transactions():
    manager = TransactionManager()

    transactions = [
        manager.begin()
        for _ in range(1000)
    ]

    assert transactions[-1].transaction_id == 1000
    assert len(
        manager.active_transactions()
    ) == 1000


def test_transaction_state_values_are_stable():
    assert TransactionState.ACTIVE.value == "ACTIVE"
    assert TransactionState.COMMITTED.value == "COMMITTED"
    assert TransactionState.ABORTED.value == "ABORTED"