SUMMARY = "RAUC OTA bundle for STM32MP157D-DK1 Capstone"
LICENSE = "CLOSED"

inherit bundle

RAUC_BUNDLE_FORMAT = "verity"
RAUC_BUNDLE_COMPATIBLE = "STM32MP157D-DK1-Capstone"
RAUC_BUNDLE_SLOTS = "rootfs"

RAUC_SLOT_rootfs = "st-image-core"
RAUC_SLOT_rootfs[fstype] = "ext4"
RAUC_SLOT_rootfs[file] = "st-image-core-openstlinux-weston-stm32mp1.rootfs.ext4"

RAUC_KEY_FILE = "/home/zybo/rauc-keys/signing.key.pem"
RAUC_CERT_FILE = "/home/zybo/rauc-keys/signing.cert.pem"
