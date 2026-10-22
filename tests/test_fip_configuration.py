import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIP_RECIPE = ROOT / "meta-local/recipes-bsp/fip-stm32mp/fip-stm32mp.bbappend"
TF_A_RECIPE = ROOT / "meta-local/recipes-bsp/trusted-firmware-a/tf-a-stm32mp_%.bbappend"
IMAGE_RECIPE = ROOT / "meta-local/recipes-st/images/st-image-core.bbappend"
INTEGRITY_SCRIPT = ROOT / "meta-local/recipes-core/boot-integrity-check/files/boot-integrity-check.sh"


class FipConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fip = FIP_RECIPE.read_text(encoding="utf-8")
        cls.tf_a = TF_A_RECIPE.read_text(encoding="utf-8")
        cls.image = IMAGE_RECIPE.read_text(encoding="utf-8")
        cls.integrity = INTEGRITY_SCRIPT.read_text(encoding="utf-8")

    def test_signing_is_enabled_across_boot_artifact_recipes(self):
        for name, source in (
            ("TF-A", self.tf_a),
            ("FIP", self.fip),
            ("image", self.image),
        ):
            with self.subTest(component=name):
                self.assertIn('SIGN_ENABLE = "1"', source)

    def test_fip_deploy_command_requests_signature(self):
        self.assertIn('FIP_PARAM_SIGN="--sign --signature-key $sign_key"', self.fip)
        self.assertIn('${FIP_WRAPPER}', self.fip)

    def test_fip_b_uses_the_fip_a_artifact_source(self):
        self.assertIn('STM32MP_SSBL2_DATA = "${STM32MP_SSBL1_DATA}"', self.image)

    def test_integrity_check_uses_a_sha256_sized_hash(self):
        match = re.search(r'^EXPECTED="([0-9a-f]+)"$', self.integrity, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(len(match.group(1)), 64)
        self.assertIn('FIP_DEV="/dev/mmcblk0p5"', self.integrity)
        self.assertIsNotNone(
            re.search(r'^FIP_LEN="[1-9][0-9]*"$', self.integrity, re.MULTILINE)
        )


if __name__ == "__main__":
    unittest.main()
