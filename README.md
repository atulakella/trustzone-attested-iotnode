# trustzone-attested-IoTNode

An IoT node built on the STM32MP157D-DK1 that combines TrustZone, OP-TEE remote attestation, boot integrity verification, and RAUC A/B OTA updates.

The project focuses on verifying boot-stage state, detecting changes to the FIP image, and recovering from failed updates on an STM32MP1 running ST's OpenSTLinux.

## What this does

- **Boot integrity:** Checks the FIP image against an expected SHA-256 hash and uses LEDs to indicate the result.
- **Remote attestation:** An OP-TEE Trusted Application (TA) measures boot-stage state and provides a challenge-response interface to a normal-world client application (CA).
- **A/B OTA:** Uses RAUC and U-Boot environment-based slot selection to update the rootfs, bootfs, and vendorfs partitions. Failed updates can trigger a switch back to the previous slot.
- **Rollback protection:** Investigates TF-A tamper-counter-based anti-rollback protection. NV-counter integration is still in progress.

This is a Yocto `meta-local` layer built on top of ST's OpenSTLinux distribution, not a standalone build environment.

## Hardware and security

Built for the STM32MP157D-DK1, which uses a Cortex-A7 application processor and a Cortex-M4 real-time processor. The current project focuses on the Linux and OP-TEE side.

The board does not have a fused TF-A ROTPK, so the boot chain does not have a hardware-enforced, fused root of trust. The FIP hash check is a software integrity check against an expected value, not a replacement for hardware-enforced secure boot.

The project demonstrates boot integrity checks and OP-TEE attestation, but does not claim complete device integrity or production-grade security.

## Repository layout

```text
meta-local/
  recipes-bsp/       TF-A, U-Boot and FIP assembly
  recipes-core/      RAUC config and boot integrity checks
  recipes-kernel/    Kernel config and device tree patches
  recipes-security/  OP-TEE attestation TA and normal-world CA
  recipes-st/images/ Image recipes and configuration
  tools/             STM32MP signing tool
  cert_create        Signing wrapper

conf-reference/      Build configuration reference
```

## Build setup

Set up ST's OpenSTLinux Yocto environment for `stm32mp1`, including Poky and the required ST layers, then add `meta-local` to `bblayers.conf`.

`conf-reference/` contains the configuration used for the actual build. Some paths are specific to the build server, so use it as a reference rather than copying it directly.

The main image targets are:

- `st-image-core`: the main RAUC A/B image.
- `core-image-capstone`: the attestation demonstration image.
- `core-image-capstone-dev`: the development variant of the attestation image.

The DK1 build uses the `optee` variant, verified on the target board.

Build the main image with:

```bash
bitbake st-image-core
```

Check the generated flash layout and partition sizes before flashing. The rootfs size and partition layout depend on the selected build configuration.

## Current status

Implemented and tested on hardware:

- FIP hash verification with an LED-based integrity demo.
- OP-TEE attestation TA with measured values and a verifier test matrix.
- RAUC A/B bundle installation.
- Slot failover tested, including a hard power cycle.
- DM-verity bundle mounting fixes.
- Slot-aware bootfs and vendorfs mounting fixes.

Still in progress:

- TF-A NV-counter anti-rollback integration. `TFW_NVCTR_VAL` and `NTFW_NVCTR_VAL` are not configured.
- Fixing the redundant U-Boot environment offsets in `/etc/fw_env.config`. Both copies currently point to the same offset.
- Handling the lack of a persistent RTC, which causes the clock to reset to approximately 2024 on each boot.

## Keys and signing

`meta-local/recipes-core/rauc/files/keyring.pem` contains the public certificate bundle used to verify RAUC update bundles.

No private keys are committed to the repository. The vendored `meta-local/tools/` signing utility is a prebuilt ELF binary from ST's signing toolchain.

The certificates and signing setup are for demonstration only. Replace the demo signing chain and review key storage and trust anchors before using this setup beyond a lab environment.

This is a demonstration project, not a production-ready security implementation, read more on my [medium post](https://medium.com/@atul.akella/i-committed-to-building-secure-hardware-into-a-final-year-project-heres-how-that-actually-went-fa16704f3c6c?sharedUserId=atul.akella).
