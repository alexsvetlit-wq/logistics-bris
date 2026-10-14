import ast
from pathlib import Path
import unittest


class CustomsFeeTest(unittest.TestCase):
    def test_import_bands_and_boundaries(self):
        tree = ast.parse(Path("streamlit_app.py").read_text(encoding="utf-8-sig"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "vat_fee_2026_rub")
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "fee", "exec"), namespace)
        fee = namespace["vat_fee_2026_rub"]
        bands = [(200000,1231),(450000,2462),(1200000,4924),(2700000,13541),
                 (4200000,18465),(5500000,21344),(10000000,49240)]
        for index, (limit, expected) in enumerate(bands):
            with self.subTest(limit=limit):
                self.assertEqual(fee(limit), expected)
                self.assertEqual(fee(limit + 0.001), expected)
                next_fee = bands[index + 1][1] if index + 1 < len(bands) else 73860
                self.assertEqual(fee(limit + 0.01), next_fee)
        self.assertEqual(fee(2200539.21), 13541)
        self.assertEqual(fee(4200000.01), 21344)
        self.assertEqual(fee(7000000), 49240)


if __name__ == "__main__":
    unittest.main()
