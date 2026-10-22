import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RECIPE = ROOT / "meta-local/recipes-bsp/trusted-firmware-a/tf-a-stm32mp_%.bbappend"


class TfANvCounterConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = RECIPE.read_text(encoding="utf-8")

    def test_counter_settings_have_safe_defaults(self):
        self.assertIn('NVCTR_ENABLE ?= "0"', self.source)
        self.assertIn('TFW_NVCTR_VAL ?= "1"', self.source)
        self.assertIn('NTFW_NVCTR_VAL ?= "1"', self.source)

    def test_enabled_counters_are_validated_before_build(self):
        self.assertIn("if d.getVar('NVCTR_ENABLE') == '1':", self.source)
        self.assertIn("for var in ('TFW_NVCTR_VAL', 'NTFW_NVCTR_VAL'):", self.source)
        self.assertIn("if not value or not value.isdigit():", self.source)
        self.assertIn("bb.fatal('%s must be a non-negative integer when NVCTR_ENABLE=1' % var)", self.source)

    def test_enabled_counters_are_passed_to_tf_a(self):
        self.assertIn(
            "TFW_NVCTR_VAL=${TFW_NVCTR_VAL} NTFW_NVCTR_VAL=${NTFW_NVCTR_VAL}",
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
