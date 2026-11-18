"""Secret escrow backed by the OS keyring.

On Windows this is Credential Manager (DPAPI-encrypted, bound to the Windows
user), so unattended jobs running as that user can read secrets without a
master password, and nothing is ever written to disk in plaintext or to git.
"""
from __future__ import annotations

import getpass

import keyring


class MissingSecret(LookupError):
    pass


def get(service: str, username: str) -> str:
    pw = keyring.get_password(service, username)
    if pw is None:
        raise MissingSecret(
            f"No secret for {username!r} in keyring service {service!r}. "
            f"Run: python -m homeit secret set {service} {username}"
        )
    return pw


def set_interactive(service: str, username: str) -> None:
    """Prompt (no echo) and store. The value never touches argv, env or logs."""
    pw = getpass.getpass(f"Password for {username} ({service}): ")
    if not pw:
        raise SystemExit("Empty password; nothing stored.")
    confirm = getpass.getpass("Confirm: ")
    if pw != confirm:
        raise SystemExit("Passwords did not match; nothing stored.")
    keyring.set_password(service, username, pw)
    print(f"Stored in {keyring.get_keyring().__class__.__name__} as {service} / {username}.")


def exists(service: str, username: str) -> bool:
    return keyring.get_password(service, username) is not None


def delete(service: str, username: str) -> None:
    keyring.delete_password(service, username)
