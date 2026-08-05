# Capstone uses the signed TF-A/FIP artifacts produced by the meta-local
# recipe append files. Keep the image-context flashlayout generator aligned
# with those deployed filenames.
FIP_SIGN_SUFFIX = "${SIGN_SUFFIX}"
# Cover optee/opteemin FSBL programmer templates (STM32MP_FSBL_PROGRAMMER_DATA / STM32MP_FSBL1_DATA); fastboot uses FIP_SIGN_SUFFIX above.
TF_A_SIGN_SUFFIX = "${SIGN_SUFFIX}"
