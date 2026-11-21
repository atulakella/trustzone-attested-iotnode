STM32MP1 FIP-A RECOVERY PACKAGE
===============================

Target: STM32MP157D-DK1, MB1272 Var3.0 Rev.C-03

BACKUPS
-------

fip-a-original.bin
  Source: /dev/mmcblk0p5 (FIP-A)
  Size: 4 MiB
  SHA-256:
  f370be0cf779505d77eaed0e9d1456ee7d41221b1e1c513c3aae8b4df21bbc2e

fip-b-original.bin
  Source: /dev/mmcblk0p6 (FIP-B)
  Size: 4 MiB
  SHA-256:
  b0336b265c73681ad89d7b1a3c367da95b37d35f5de183bade60bc8dee0de2e9

Both backups begin with the November 16 signed SD-card FIP
(SHA-256 bd71e41a63af6b2e61062c20776fcbadff0e6606c5c4e67027c4d20cb369728d).
The complete 4 MiB partition images are retained, including trailing
partition bytes.

VERIFY
------

Run before any restore operation:
  sha256sum -c SHA256SUMS

RESTORE TARGET
--------------

The immediate recovery target after the FIP-A tamper test is FIP-A:
  Linux partition: /dev/mmcblk0p5
  Flash-layout partition ID: 0x08
  Flash-layout byte offset: 0x00104400
  Payload: fip-a-original.bin

FIP-B backup:
  Linux partition: /dev/mmcblk0p6
  Flash-layout partition ID: 0x09
  Flash-layout byte offset: 0x00504400
  Payload: fip-b-original.bin

IMPORTANT
---------

These are raw 4 MiB partition backups, not 1.8 MiB standalone FIP
files. Preserve the full 4 MiB partition size when restoring.

Do not run a write command until the selected USB programming method,
payload handling, addressing, and read-back verification procedure
have been validated.

Do not assume automatic fallback to FIP-B if FIP-A authentication
fails. The live FWU metadata showed active_index=0 (FIP-A).
