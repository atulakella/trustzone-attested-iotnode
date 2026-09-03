SIGN_ENABLE = "1"
SIGN_KEY_stm32mp15 = "/home/zybo/keys/stm32mp1-boot-signing/tfa_boot_ecdsa.pem"
SIGN_KEY_stm32mp13 = "/home/zybo/keys/stm32mp1-boot-signing/tfa_boot_ecdsa.pem"
SIGN_TOOL = "/mnt/storage/stm32mp1-workspace/meta-local/cert_create"
EXTRA_OEMAKE += "KEY_ALG=ecdsa"
SIGN_TOOL_EXTRA_stm32mp15 += " -a ecdsa"

NVCTR_ENABLE ?= "0"
TFW_NVCTR_VAL ?= "1"
NTFW_NVCTR_VAL ?= "1"
EXTRA_OEMAKE += "${@bb.utils.contains('NVCTR_ENABLE', '1', 'TFW_NVCTR_VAL=${TFW_NVCTR_VAL} NTFW_NVCTR_VAL=${NTFW_NVCTR_VAL}', '', d)}"

do_compile:prepend() {
    export PATH="/mnt/storage/stm32mp1-workspace/meta-local:${PATH}"
}
