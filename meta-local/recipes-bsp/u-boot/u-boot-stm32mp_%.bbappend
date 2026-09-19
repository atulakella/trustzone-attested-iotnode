FILESEXTRAPATHS:prepend := "${THISDIR}/u-boot-stm32mp:"

SRC_URI += "file://bootcount-enable.cfg"
SRC_URI += "file://0001-rauc-bootsel-override.patch"

do_generate_defconfig:append() {
    for config in $(echo ${UBOOT_MACHINE} | tr ' ' '\n' | sort -u); do
        if ! grep -q "CONFIG_CMD_BOOTCOUNT" ${S}/configs/${config}; then
            cat ${WORKDIR}/bootcount-enable.cfg >> ${S}/configs/${config}
        fi
    done
}
