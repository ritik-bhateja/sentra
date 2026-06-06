"""Property-based tests for role_sync.py.

Covers three correctness properties:

Property 6: Synchronization covers all RDS users and defaults new ones
    - After sync, every RDS email exists in Keycloak.
    - Newly created users hold DEFAULT_ROLE.
    Validates: Requirements 4.1, 4.4, 12.1

Property 7: Synchronization is idempotent for existing users
    - Running sync leaves existing users' roles unchanged.
    - No duplicates are created.
    Validates: Requirements 4.3

Property 8: Synchronization accounting is exact
    - created == |new emails|
    - skipped == |existing emails|
    - created + skipped == total processed
    Validates: Requirements 4.6
"""

import sys
import os
from unittest.mock import MagicMock
from typing import Optional

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure BackendAPI is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth.roles import DEFAULT_ROLE, Role
from auth.keycloak_client import KeycloakClient, KeycloakUnavailable
from role_sync import sync_users


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

# Generate valid-looking email addresses
email_strategy = st.from_regex(
    r"[a-z][a-z0-9]{0,15}@[a-z]{1,8}\.[a-z]{2,4}", fullmatch=True
)

# Generate sets of unique emails (representing RDS users)
email_set_strategy = st.frozensets(email_strategy, min_size=1, max_size=30)

# Generate a subset fraction for pre-existing users
subset_fraction_strategy = st.floats(min_value=0.0, max_value=1.0)


# --------------------------------------------------------------------------
# FakeKeycloak: in-memory Keycloak substitute for property tests
# --------------------------------------------------------------------------


class FakeKeycloak:
    """In-memory Keycloak substitute for testing sync logic.

    Tracks users and their role assignments without any network calls.
    """

    def __init__(self, existing_users: Optional[dict[str, list[str]]] = None):
        """
        Args:
            existing_users: Mapping of email -> list of assigned role names.
                            Represents users already in Keycloak before sync.
        """
        # email -> user_id
        self._users: dict[str, str] = {}
        # user_id -> list of role names
        self._roles: dict[str, list[str]] = {}

        # Counter for generating unique user IDs
        self._id_counter = 0

        if existing_users:
            for email, roles in existing_users.items():
                uid = self._next_id()
                self._users[email] = uid
                self._roles[uid] = list(roles)

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"kc-user-{self._id_counter}"

    def user_exists(self, email: str) -> bool:
        return email in self._users

    def create_user(self, email: str) -> str:
        if email in self._users:
            return self._users[email]
        uid = self._next_id()
        self._users[email] = uid
        self._roles[uid] = []
        return uid

    def assign_realm_role(self, user_id: str, role: Role) -> None:
        if user_id not in self._roles:
            self._roles[user_id] = []
        self._roles[user_id].append(role.value)

    def get_roles_for_email(self, email: str) -> list[str]:
        uid = self._users.get(email)
        if uid is None:
            return []
        return list(self._roles.get(uid, []))

    def get_all_emails(self) -> set[str]:
        return set(self._users.keys())


def _make_fake_client(fake_kc: FakeKeycloak) -> KeycloakClient:
    """Create a KeycloakClient whose methods delegate to FakeKeycloak."""
    client = KeycloakClient()
    client.enabled = True
    client.user_exists = fake_kc.user_exists
    client.create_user = fake_kc.create_user
    client.assign_realm_role = fake_kc.assign_realm_role
    return client


def _make_fake_db(emails: set[str]):
    """Create a fake DB session that returns User objects with given emails."""
    users = []
    for email in emails:
        user = MagicMock()
        user.email = email
        users.append(user)

    db = MagicMock()
    db.query.return_value.all.return_value = users
    return db


# --------------------------------------------------------------------------
# Property 6: Synchronization covers all RDS users and defaults new ones
# Validates: Requirements 4.1, 4.4, 12.1
# --------------------------------------------------------------------------


class TestSyncCoverageAndDefaultRole:
    """Property 6: After sync, every RDS email exists in Keycloak and
    newly created users hold DEFAULT_ROLE."""

    @given(
        all_emails=email_set_strategy,
        pre_existing_fraction=subset_fraction_strategy,
    )
    @settings(max_examples=300)
    def test_all_rds_users_exist_in_keycloak_after_sync(
        self, all_emails: frozenset[str], pre_existing_fraction: float
    ):
        """Every RDS user email exists in Keycloak after sync runs."""
        emails = sorted(all_emails)
        split = int(len(emails) * pre_existing_fraction)
        pre_existing = set(emails[:split])

        # Set up FakeKeycloak with pre-existing users (arbitrary roles)
        existing_map = {e: ["admin"] for e in pre_existing}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        sync_users(client, db)

        # Every email from RDS must now exist in Keycloak
        for email in all_emails:
            assert fake_kc.user_exists(email), (
                f"Email {email} missing from Keycloak after sync"
            )

    @given(
        all_emails=email_set_strategy,
        pre_existing_fraction=subset_fraction_strategy,
    )
    @settings(max_examples=300)
    def test_newly_created_users_have_default_role(
        self, all_emails: frozenset[str], pre_existing_fraction: float
    ):
        """Newly created Keycloak users are assigned DEFAULT_ROLE."""
        emails = sorted(all_emails)
        split = int(len(emails) * pre_existing_fraction)
        pre_existing = set(emails[:split])
        new_emails = all_emails - pre_existing

        existing_map = {e: ["viewer_with_query"] for e in pre_existing}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        sync_users(client, db)

        # Every newly created user must have DEFAULT_ROLE assigned
        for email in new_emails:
            roles = fake_kc.get_roles_for_email(email)
            assert DEFAULT_ROLE.value in roles, (
                f"New user {email} does not have DEFAULT_ROLE; has: {roles}"
            )


# --------------------------------------------------------------------------
# Property 7: Synchronization is idempotent for existing users
# Validates: Requirements 4.3
# --------------------------------------------------------------------------


class TestSyncIdempotency:
    """Property 7: Running sync leaves existing users' roles unchanged
    and creates no duplicates."""

    @given(
        all_emails=email_set_strategy,
        role_choice=st.sampled_from([
            "admin", "viewer_with_query", "viewer_without_query"
        ]),
    )
    @settings(max_examples=300)
    def test_existing_users_roles_unchanged(
        self, all_emails: frozenset[str], role_choice: str
    ):
        """Pre-existing Keycloak users keep their original roles after sync."""
        # All emails pre-exist with an arbitrary role
        existing_map = {e: [role_choice] for e in all_emails}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        # Capture roles before sync
        roles_before = {e: fake_kc.get_roles_for_email(e) for e in all_emails}

        sync_users(client, db)

        # Roles must remain identical
        for email in all_emails:
            roles_after = fake_kc.get_roles_for_email(email)
            assert roles_after == roles_before[email], (
                f"Roles changed for {email}: {roles_before[email]} -> {roles_after}"
            )

    @given(
        all_emails=email_set_strategy,
        pre_existing_fraction=subset_fraction_strategy,
    )
    @settings(max_examples=300)
    def test_no_duplicates_after_sync(
        self, all_emails: frozenset[str], pre_existing_fraction: float
    ):
        """After sync, each email appears exactly once in Keycloak."""
        emails = sorted(all_emails)
        split = int(len(emails) * pre_existing_fraction)
        pre_existing = set(emails[:split])

        existing_map = {e: ["admin"] for e in pre_existing}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        sync_users(client, db)

        # Total users in Keycloak should equal unique RDS emails
        kc_emails = fake_kc.get_all_emails()
        assert len(kc_emails) == len(all_emails), (
            f"Duplicate users detected: {len(kc_emails)} KC users for "
            f"{len(all_emails)} RDS emails"
        )

    @given(all_emails=email_set_strategy)
    @settings(max_examples=200)
    def test_running_sync_twice_is_idempotent(self, all_emails: frozenset[str]):
        """Running sync twice yields the same state as running it once."""
        fake_kc = FakeKeycloak()
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        # First sync
        sync_users(client, db)
        state_after_first = {
            e: fake_kc.get_roles_for_email(e) for e in all_emails
        }

        # Second sync
        summary = sync_users(client, db)
        state_after_second = {
            e: fake_kc.get_roles_for_email(e) for e in all_emails
        }

        # State should be identical
        assert state_after_first == state_after_second
        # Second run should create nothing
        assert summary["created"] == 0
        assert summary["skipped"] == len(all_emails)


# --------------------------------------------------------------------------
# Property 8: Synchronization accounting is exact
# Validates: Requirements 4.6
# --------------------------------------------------------------------------


class TestSyncAccounting:
    """Property 8: The sync summary accurately reports created/skipped counts."""

    @given(
        all_emails=email_set_strategy,
        pre_existing_fraction=subset_fraction_strategy,
    )
    @settings(max_examples=300)
    def test_created_equals_new_emails(
        self, all_emails: frozenset[str], pre_existing_fraction: float
    ):
        """created count equals the number of emails not pre-existing."""
        emails = sorted(all_emails)
        split = int(len(emails) * pre_existing_fraction)
        pre_existing = set(emails[:split])
        expected_new = len(all_emails) - len(pre_existing)

        existing_map = {e: ["admin"] for e in pre_existing}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        summary = sync_users(client, db)

        assert summary["created"] == expected_new, (
            f"Expected {expected_new} created, got {summary['created']}"
        )

    @given(
        all_emails=email_set_strategy,
        pre_existing_fraction=subset_fraction_strategy,
    )
    @settings(max_examples=300)
    def test_skipped_equals_existing_emails(
        self, all_emails: frozenset[str], pre_existing_fraction: float
    ):
        """skipped count equals the number of emails already in Keycloak."""
        emails = sorted(all_emails)
        split = int(len(emails) * pre_existing_fraction)
        pre_existing = set(emails[:split])
        expected_skipped = len(pre_existing)

        existing_map = {e: ["viewer_without_query"] for e in pre_existing}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        summary = sync_users(client, db)

        assert summary["skipped"] == expected_skipped, (
            f"Expected {expected_skipped} skipped, got {summary['skipped']}"
        )

    @given(
        all_emails=email_set_strategy,
        pre_existing_fraction=subset_fraction_strategy,
    )
    @settings(max_examples=300)
    def test_created_plus_skipped_equals_total(
        self, all_emails: frozenset[str], pre_existing_fraction: float
    ):
        """created + skipped == total RDS users processed (no errors case)."""
        emails = sorted(all_emails)
        split = int(len(emails) * pre_existing_fraction)
        pre_existing = set(emails[:split])

        existing_map = {e: ["admin"] for e in pre_existing}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        summary = sync_users(client, db)

        total = summary["created"] + summary["skipped"] + len(summary["errors"])
        assert total == len(all_emails), (
            f"Accounting mismatch: {summary['created']} + {summary['skipped']} "
            f"+ {len(summary['errors'])} != {len(all_emails)}"
        )

    @given(all_emails=email_set_strategy)
    @settings(max_examples=200)
    def test_all_new_users_accounting(self, all_emails: frozenset[str]):
        """When no users pre-exist, created == total and skipped == 0."""
        fake_kc = FakeKeycloak()
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        summary = sync_users(client, db)

        assert summary["created"] == len(all_emails)
        assert summary["skipped"] == 0
        assert len(summary["errors"]) == 0

    @given(all_emails=email_set_strategy)
    @settings(max_examples=200)
    def test_all_existing_users_accounting(self, all_emails: frozenset[str]):
        """When all users pre-exist, created == 0 and skipped == total."""
        existing_map = {e: ["viewer_with_query"] for e in all_emails}
        fake_kc = FakeKeycloak(existing_users=existing_map)
        client = _make_fake_client(fake_kc)
        db = _make_fake_db(all_emails)

        summary = sync_users(client, db)

        assert summary["created"] == 0
        assert summary["skipped"] == len(all_emails)
        assert len(summary["errors"]) == 0

    def test_errors_are_counted_correctly(self):
        """Users that fail are recorded in the errors list."""
        emails = {"ok@test.com", "fail@test.com", "ok2@test.com"}

        fake_kc = FakeKeycloak()
        client = _make_fake_client(fake_kc)

        # Override user_exists to raise for one specific email
        original_user_exists = fake_kc.user_exists

        def flaky_user_exists(email):
            if email == "fail@test.com":
                raise KeycloakUnavailable("Simulated failure")
            return original_user_exists(email)

        client.user_exists = flaky_user_exists
        db = _make_fake_db(emails)

        summary = sync_users(client, db)

        assert len(summary["errors"]) == 1
        assert summary["errors"][0][0] == "fail@test.com"
        assert summary["created"] + summary["skipped"] + len(summary["errors"]) == 3
