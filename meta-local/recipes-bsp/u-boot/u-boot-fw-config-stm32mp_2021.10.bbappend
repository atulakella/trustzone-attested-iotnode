PR:append = ".2"
do_install:append () {
    ln -sf fw_env.config.mmc ${D}${sysconfdir}/fw_env.config
    sed -i '0,/-0x2000/! s/-0x2000/-0x4000/' ${D}${sysconfdir}/fw_env.config.mmc
}
