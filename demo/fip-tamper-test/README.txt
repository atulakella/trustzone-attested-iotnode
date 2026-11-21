STM32MP1 FIP-A TAMPER TEST
==========================

Target: STM32MP157D-DK1, MB1272 Var3.0 Rev.C-03
Target partition: FIP-A (/dev/mmcblk0p5)
Flash-layout byte offset: 0x00104400
Program payload: fip-a-tampered.bin

PAYLOAD
-------

fip-a-tampered.bin is a raw 4 MiB image of the complete FIP-A
partition. It was derived from the original 4 MiB FIP-A backup.

One byte inside the signed FIP's BL33 payload was modified. The
remaining partition bytes are unchanged.

Mutation:
  FIP offset:       0x80E2C
  BL33-relative:    0x100
  Original byte:    0x0D
  Modified byte:    0x0C
  Partition offset: 0x80E2C

fip-bl33-tamper.bin is an older standalone tampered FIP artifact.
It is NOT referenced by the TSV and is NOT the programming payload.

VERIFY
------

Run before use:
  sha256sum -c SHA256SUMS

The TSV selects only FIP-A (ID 0x08) for programming. All other
partition rows are disabled. Inspect the TSV before any operation.

SAFETY
------

Do not program this package until the STM32CubeProgrammer handling
of a 4 MiB payload with Type=FIP, the TSV path resolution, and the
USB programming and recovery procedures have been independently
validated.

Expected negative-test evidence:
  TF-A BL2 rejects the modified BL33 authentication.
  BL2 must not proceed to "BL2: Booting BL32".

This tests configured software image authentication. It does not
demonstrate OTP-pinned ROTPK or hardware-rooted secure boot.
