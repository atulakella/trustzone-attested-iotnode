FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://0001-dts-enable-UART7-for-ESP32-link-PE7-PE8-pins-already.patch"

SRC_URI += "file://0001-dts-add-demo-leds-red-green-PA13-PA14.patch"
SRC_URI += "file://dm-verity.cfg"
KERNEL_CONFIG_FRAGMENTS:append:stm32mp1common = " ${WORKDIR}/dm-verity.cfg"
SRC_URI += "file://custom-version.cfg"
KERNEL_CONFIG_FRAGMENTS:append:stm32mp1common = " ${WORKDIR}/custom-version.cfg"
