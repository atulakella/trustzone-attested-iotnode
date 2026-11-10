#!/usr/bin/env python3

import secrets
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR))

from verify import (
    load_allowlist,
    load_pubkey,
    extract_evidence,
    verify,
)


def main():
    pubkey = load_pubkey(str(DEMO_DIR / "pubkey.pem"))
    tee_allow = load_allowlist(str(DEMO_DIR / "tee-allow.txt"))
    ta_allow = load_allowlist(str(DEMO_DIR / "ta-allow.txt"))

    nonce = secrets.token_bytes(32)
    nonce_hex = nonce.hex()

    print()
    print("=" * 70)
    print("REMOTE ATTESTATION — MANUAL VERIFIER")
    print("=" * 70)
    print()
    print("FRESH CHALLENGE")
    print()
    print(f"Nonce:\n{nonce_hex}")
    print()
    print("Copy this nonce to the BOARD and run:")
    print()
    print(f"    attest_ca {nonce_hex}")
    print()
    print("Then paste the complete evidence output below.")
    print("Finish with an empty line.")
    print()

    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)

    try:
        blob = extract_evidence("\n".join(lines))
        ev = verify(
            blob,
            nonce,
            pubkey,
            tee_allow,
            ta_allow,
        )
    except Exception as exc:
        print()
        print("REJECTED")
        print(f"Reason: {exc}")
        return 1

    print()
    print("=" * 70)
    print("ATTESTATION VALID")
    print("=" * 70)
    print()
    print(f"Evidence length : {len(blob)} bytes")
    print(f"TEE hash        : {ev.tee_hash.hex()}")
    print(f"TA UUID         : {ev.ta_uuid.hex()}")
    print(f"TA hash         : {ev.ta_hash.hex()}")
    print(f"Signature       : {len(ev.sig)} bytes")
    print()


if __name__ == "__main__":
    raise SystemExit(main())