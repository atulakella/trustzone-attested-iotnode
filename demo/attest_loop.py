#!/usr/bin/env python3
"""
Core logic for the STM32MP1 remote-attestation demo.

This module:
  - generates fresh nonces
  - SSHes to the STM32MP157D-DK1
  - invokes attest_ca <nonce> under strace to capture the TEE call chain
  - extracts the returned evidence
  - verifies it using the existing verify.py implementation
  - optionally tampers with evidence for the live demo

The TUI is intentionally kept separate in tui.py.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime

import paramiko

from verify import (
    VerifyError,
    extract_evidence,
    load_allowlist,
    load_pubkey,
    verify,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BOARD_HOST = "192.168.137.2"
BOARD_USER = "root"

BOARD_ATTEST_CA = "/usr/bin/attest_ca"
STRACE_OUT     = "/tmp/attest_trace.txt"

PUBKEY_FILE    = "pubkey.pem"
TEE_ALLOW_FILE = "tee-allow.txt"
TA_ALLOW_FILE  = "ta-allow.txt"

ATTESTATION_INTERVAL = 120


# ---------------------------------------------------------------------------
# Trace dataclass
# ---------------------------------------------------------------------------

@dataclass
class TraceInfo:
    """Parsed highlights from the strace output of one attest_ca run."""

    tee_driver_opened: bool = False        # openat /dev/tee0
    optee_caps: str         = ""           # TEE_IOC_VERSION impl_caps field
    session_uuid: str       = ""           # TEE_IOC_OPEN_SESSION uuid
    session_ret: str        = ""           # ret_origin from OPEN_SESSION
    nonce_shm_size: str     = ""           # SHM_REGISTER size for nonce (0x20)
    invoke_ret: str         = ""           # ret from TEE_IOC_INVOKE
    invoke_origin: str      = ""           # ret_origin from TEE_IOC_INVOKE
    invoke_out_size: str    = ""           # output size returned (0x1fa = 506)
    session_closed: bool    = False        # TEE_IOC_CLOSE_SESSION seen
    raw: str                = ""           # full strace text for raw view


def parse_trace(raw: str) -> TraceInfo:
    """Extract the meaningful security-relevant fields from strace output."""

    t = TraceInfo(raw=raw)

    for line in raw.splitlines():

        # /dev/tee0 opened
        if '/dev/tee0' in line and 'openat' in line:
            t.tee_driver_opened = True

        # TEE_IOC_VERSION — grab impl_caps
        if 'TEE_IOC_VERSION' in line:
            m = re.search(r'impl_caps=(\S+?)[\},]', line)
            if m:
                t.optee_caps = m.group(1)

        # TEE_IOC_OPEN_SESSION — grab uuid and ret_origin
        if 'TEE_IOC_OPEN_SESSION' in line:
            m = re.search(r'uuid=([\w-]+)', line)
            if m:
                t.session_uuid = m.group(1)
            m = re.search(r'ret_origin=(\w+)', line)
            if m:
                t.session_ret = m.group(1)

        # TEE_IOC_SHM_REGISTER — first one is the nonce (0x20 = 32 bytes)
        if 'TEE_IOC_SHM_REGISTER' in line and not t.nonce_shm_size:
            m = re.search(r'length=(0x[\da-fA-F]+)', line)
            if m:
                t.nonce_shm_size = m.group(1)

        # TEE_IOC_INVOKE — ret, ret_origin, output size
        if 'TEE_IOC_INVOKE' in line:
            # ret_origin (last occurrence = the => result side)
            origins = re.findall(r'ret_origin=(\w+)', line)
            if origins:
                t.invoke_origin = origins[-1]
            rets = re.findall(r'\bret=(\d+)', line)
            if rets:
                t.invoke_ret = rets[-1]
            # output size is the second shm_id=2 MEMREF_OUTPUT size
            out_sizes = re.findall(
                r'MEMREF_OUTPUT.*?size=(0x[\da-fA-F]+)', line
            )
            if out_sizes:
                t.invoke_out_size = out_sizes[-1]

        # TEE_IOC_CLOSE_SESSION
        if 'TEE_IOC_CLOSE_SESSION' in line:
            t.session_closed = True

    return t


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class AttestationResult:
    timestamp: datetime
    nonce:     str
    passed:    bool
    reason:    str
    evidence:  bytes | None = None
    trace:     TraceInfo | None = None


# ---------------------------------------------------------------------------
# Verifier setup
# ---------------------------------------------------------------------------

def load_verifier():
    """Load the pinned public key and static allowlists once."""

    pubkey    = load_pubkey(PUBKEY_FILE)
    tee_allow = load_allowlist(TEE_ALLOW_FILE)
    ta_allow  = load_allowlist(TA_ALLOW_FILE)

    return pubkey, tee_allow, ta_allow


# ---------------------------------------------------------------------------
# SSH
# ---------------------------------------------------------------------------

def connect_to_board() -> paramiko.SSHClient:
    """Create an SSH connection to the STM32MP1 board."""

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    transport = paramiko.Transport((BOARD_HOST, 22))
    transport.connect()
    transport.auth_none(BOARD_USER)

    client._transport = transport

    return client


def _run(client: paramiko.SSHClient, cmd: str) -> str:
    """Run a command and return stdout text. Raises on non-zero exit."""

    _, stdout, stderr = client.exec_command(cmd)
    out  = stdout.read().decode("utf-8", errors="replace")
    err  = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()

    if code != 0:
        raise RuntimeError(
            f"command failed (exit {code}): {cmd!r}\n{err.strip() or out.strip()}"
        )

    return out


def fetch_evidence(nonce_hex: str) -> tuple[str, bytes, TraceInfo]:
    """
    Run attest_ca under strace on the board.

    Returns:
        (board_returned_nonce, evidence_bytes, trace_info)
    """

    client = connect_to_board()

    try:
        # Run attest_ca under strace; strace writes to file, attest_ca
        # stdout (nonce= / evidence=) comes through the channel normally.
        cmd = (
            f"strace -e trace=openat,ioctl "
            f"-o {STRACE_OUT} "
            f"{BOARD_ATTEST_CA} {nonce_hex}"
        )

        stdout_text = _run(client, cmd)

        # Pull the strace output back separately.
        try:
            trace_raw = _run(client, f"cat {STRACE_OUT}")
        except Exception:
            trace_raw = ""

        # Parse nonce from attest_ca stdout.
        returned_nonce = None
        for line in stdout_text.splitlines():
            line = line.strip()
            if line.startswith("nonce="):
                returned_nonce = line[len("nonce="):]

        if returned_nonce is None:
            raise RuntimeError("attest_ca output did not contain nonce=")

        evidence = extract_evidence(stdout_text)
        trace    = parse_trace(trace_raw)

        return returned_nonce, evidence, trace

    finally:
        client.close()


# ---------------------------------------------------------------------------
# Tamper mode
# ---------------------------------------------------------------------------

def tamper_evidence(evidence: bytes) -> bytes:
    """
    Flip one byte in the signature.

    Leaves the evidence structurally valid but makes the RSA signature
    invalid — clean cryptographic failure for the demo.
    """

    if len(evidence) < 1:
        raise ValueError("cannot tamper with empty evidence")

    tampered = bytearray(evidence)

    # Signature begins at byte 122 in the RAT1 v1 format.
    signature_offset = 122

    if len(tampered) <= signature_offset:
        raise ValueError("evidence is too short to contain a signature")

    tampered[signature_offset] ^= 0x01

    return bytes(tampered)


# ---------------------------------------------------------------------------
# One attestation
# ---------------------------------------------------------------------------

def attest_once(
    pubkey,
    tee_allow,
    ta_allow,
    tamper: bool = False,
) -> AttestationResult:
    """Perform exactly one complete attestation transaction."""

    timestamp  = datetime.now()
    nonce_bytes = secrets.token_bytes(32)
    nonce_hex   = nonce_bytes.hex()
    trace       = None

    try:
        returned_nonce, evidence, trace = fetch_evidence(nonce_hex)

        if returned_nonce.lower() != nonce_hex.lower():
            return AttestationResult(
                timestamp=timestamp,
                nonce=nonce_hex,
                passed=False,
                reason="board returned a different nonce",
                evidence=evidence,
                trace=trace,
            )

        if tamper:
            evidence = tamper_evidence(evidence)

        verify(evidence, nonce_bytes, pubkey, tee_allow, ta_allow)

        return AttestationResult(
            timestamp=timestamp,
            nonce=nonce_hex,
            passed=True,
            reason="Attestation verified",
            evidence=evidence,
            trace=trace,
        )

    except VerifyError as exc:
        return AttestationResult(
            timestamp=timestamp,
            nonce=nonce_hex,
            passed=False,
            reason=exc.reason,
            evidence=evidence if "evidence" in locals() else None,
            trace=trace,
        )

    except Exception as exc:
        return AttestationResult(
            timestamp=timestamp,
            nonce=nonce_hex,
            passed=False,
            reason=f"{type(exc).__name__}: {exc}",
            evidence=None,
            trace=trace,
        )


# ---------------------------------------------------------------------------
# Simple CLI/debug entry point
# ---------------------------------------------------------------------------

def main():
    print("Loading attestation verifier...")

    pubkey, tee_allow, ta_allow = load_verifier()

    print(f"Connecting to {BOARD_HOST}...")
    print("Running one attestation...")

    result = attest_once(pubkey, tee_allow, ta_allow)

    print()
    print("PASS" if result.passed else "FAIL")
    print(f"timestamp: {result.timestamp:%Y-%m-%d %H:%M:%S}")
    print(f"nonce:     {result.nonce}")
    print(f"reason:    {result.reason}")

    if result.trace:
        t = result.trace
        print()
        print(f"tee_driver_opened : {t.tee_driver_opened}")
        print(f"optee_caps        : {t.optee_caps}")
        print(f"session_uuid      : {t.session_uuid}")
        print(f"invoke_origin     : {t.invoke_origin}")
        print(f"invoke_out_size   : {t.invoke_out_size}")
        print(f"session_closed    : {t.session_closed}")


if __name__ == "__main__":
    main()