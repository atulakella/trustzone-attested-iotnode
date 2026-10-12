SUMMARY = "Demo-only FIP integrity check (compensating control for TBB bypass)"
DESCRIPTION = "Hashes the FIP partition at early boot and halts with a \
visual LED indicator if it doesn't match the known-good hash. This is a \
demo-level compensating control, not a fix for the underlying TF-A \
ROTPK_NOT_DEPLOYED / stm32mp_is_auth_supported() verification bypass."
LICENSE = "CLOSED"

SRC_URI = " \
    file://boot-integrity-check.sh \
    file://boot-integrity-check.service \
"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "boot-integrity-check.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/boot-integrity-check.sh ${D}${bindir}/boot-integrity-check.sh

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/boot-integrity-check.service ${D}${systemd_system_unitdir}/boot-integrity-check.service
}

FILES:${PN} += " \
    ${bindir}/boot-integrity-check.sh \
    ${systemd_system_unitdir}/boot-integrity-check.service \
"
