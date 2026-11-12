# Demo Guide

This covers the live demo sequence for the TrustZone-attested IoT node project on the STM32MP157D-DK1. Five demos, run in a fixed order. Each one proves a specific claim about the boot chain, the attestation flow, or the OTA/rollback setup. None of them is a general health check of the board, so read the "what it proves" line for each one carefully.

## Board and network info

- Board: STM32MP157D-DK1, STM32MP157DAC Rev.Z, MB1272 Var3.0 Rev.C-03
- Board IP: `192.168.137.2`
- Board hostname: `stm32mp1-e5-5a-31`
- Serial console: `ttySTM0`, 115200 baud
- Build server: Yocto workspace on a separate Linux host, used only to regenerate FIP/TF-A/kernel artifacts, not needed to run the demos themselves

## Demo order and time budget

| # | Demo | Time (live) | Needs a reflash? |
|---|------|-------------|-------------------|
| 1 | Attestation (TUI) | 1-2 min | No |
| 2 | Replay rejection | 1-2 min | No |
| 3 | A/B failover and reset | 2-3 min | No (uses existing slots) |
| 4 | OTA bundle install | 3-5 min | No (uses a prebuilt bundle) |
| 5 | FIP tamper test | 5-8 min if live, less with captured logs | Yes, twice (tamper + restore) |

If you are short on time, demo 5 is the one to swap for captured UART logs instead of a live run. The result is deterministic, so a captured log carries the same weight as a live run, and it removes the reflash risk right before you go on stage.

## Demo 1: Attestation (TUI)

**What it proves:** the board can produce a signed attestation report from inside the secure world (OP-TEE), and a host-side verifier can check that signature against the board's public key.

**What it does not prove:** that the board's identity key is independently trustworthy. The host currently trusts the board's runtime public key as given, it does not verify the key itself came from a provisioned, tamper-proof source. That is a separate open question in the trust model.

**Files needed in the demo folder:**
- `tui.py`
- `verify.py`
- `pubkey.pem`
- `attest_loop.py` (if the TUI calls into it)

**How to run:** SSH into the board, run the TUI client, let it produce evidence, and run the verifier against it. Expect a clear pass/fail line at the end.

## Demo 2: Replay rejection

**What it proves:** captured, previously-valid attestation evidence is rejected on a second submission, because the nonce no longer matches.

**What it does not prove:** protection against anything other than replay. A compromised board can still produce fresh, validly signed evidence for anything it wants to claim.

**Files needed in the demo folder:**
- Same as demo 1, plus a copy of previously captured evidence to replay
- `ta-allow.txt` / `tee-allow.txt` if the verifier checks against an allowlist

**How to run:** capture one evidence sample, verify it once (should pass), then submit the exact same evidence again (should fail with a nonce mismatch).

## Demo 3: A/B failover and reset

**What it proves:** the board has two independent, bootable rootfs slots, and the boot loader will automatically fall back to the other slot if the active one is marked bad or runs out of boot attempts.

**What it does not prove, unless specifically called out:** do not describe a manually forced slot switch as proof of automatic rollback after a real failure. Those are two different things. A genuine failed-boot test (letting a slot actually fail to boot and watching the counter exhaust on its own) is a separate, higher-risk test and is not part of this sequence unless you choose to run it.

**Files needed in the demo folder:**
- `demo-reset.sh` (resets both slot counters and boot order to a known baseline, does not touch FIP or flash)

**How to run:** check current slot and boot status, force a switch if you want to show the other slot, then run the reset script to return to a clean baseline for the next person.

## Demo 4: OTA bundle install

**What it proves:** a signed, verity-protected update bundle can be installed to the inactive slot over the network, and the board will boot into the newly installed slot afterward.

**Scope:** this bundle updates the rootfs only. It does not touch the boot partition or the vendor partition.

**Files needed in the demo folder:**
- The `.raucb` bundle file (keep the exact filename, it is timestamped)
- Any version marker file you are using to show the update actually changed something visible (for example a version string printed after boot)

**How to run:** confirm current active slot, run the install command, watch it copy and verify the image, then reboot and confirm the board is now running from the other slot.

## Demo 5: FIP tamper test

**What it proves:** whether the boot chain's signature verification at the firmware image package (FIP) level actually rejects a corrupted certificate signature, or not. This project found that it does not reject it, on this specific board and firmware revision, because the board is not fuse-provisioned with a root of trust key. That is a real finding, not a bug in the demo. Frame it as a finding about the current trust state of the board, not as "secure boot is broken" in general.

**What it needs:**
- A known-good FIP binary for this board, hashed and verified
- A tampered copy of that FIP, with exactly one byte flipped inside a certificate signature, also hashed and verified
- The full flash layout file (TSV) for this board, unmodified, so the full partition table is written correctly every time
- The bootstrap binaries referenced by that TSV (the small files used only to get past the first stage of flashing over USB)
- A way to capture the UART log for both the clean run and the tampered run, so you can compare them side by side

**Important lesson learned while preparing this:** do not flash with a partition table file that only lists a few rows. The programming tool treats whatever rows you give it as the entire partition table and will drop every partition not listed. Always flash with the complete, unmodified partition table file, and only change the content of the one row you actually want to test. If you need to recover from a partial partition table, reflash with the complete, hash-verified package you already built earlier, and confirm all partitions are back before doing anything else.

**How to run:**
1. Hash-check both FIP files against known values before touching the board.
2. Flash the clean FIP using the full partition table file, with only that one row's binary path changed.
3. Boot and capture the UART log. Confirm it reaches the normal boot prompt.
4. Flash the tampered FIP the same way.
5. Boot and capture the UART log again. Compare the two logs.
6. Flash the clean FIP back before you consider the board done. Do not leave it sitting on the tampered FIP.

## Folder layout

A clean demo folder should look roughly like this before you start:

```
demo/
  tui.py
  verify.py
  attest_loop.py
  pubkey.pem
  ta-allow.txt
  tee-allow.txt
  <ota-bundle>.raucb
  demo-reset.sh
  fip-tamper-test/
    fip-clean-current.bin
    fip-tampered-current.bin
    SHA256SUMS-current.txt
    flash-clean.tsv  (or the full board TSV, with only fip-a's path changed)
    flash-tampered.tsv
    <bootstrap binaries referenced by the TSV>
```

## General notes

- Always verify a file's hash after copying it anywhere, before you flash it or run it. This has saved real debugging time more than once.
- Keep a clean reset path ready before you run anything that changes boot state. Know how you are getting back to a known-good board before you start.
- If something fails mid-flash over USB, it is often a transient link issue, not a content problem. Retry once with the exact same files before assuming something is actually wrong.
