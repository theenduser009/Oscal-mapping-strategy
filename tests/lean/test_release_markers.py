"""Prevent mismatched seven-cell mapper release markers."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CELLS = ROOT / "notebooks" / "cells"

class ReleaseMarkerTests(unittest.TestCase):
    def test_compiler_helpers_builder_and_orchestrator_match(self):
        cell3 = (CELLS / "03_canonical_mapping_contract.py").read_text(encoding="utf-8")
        cell4 = (CELLS / "04_parsing_transform_payload_helpers.py").read_text(encoding="utf-8")
        cell5 = (CELLS / "05_registry_graph_builder.py").read_text(encoding="utf-8")
        cell7 = (CELLS / "07_mapper_orchestrator.py").read_text(encoding="utf-8")

        release = re.search(r'LEAN_MAPPER_RELEASE = "([^"]+)"', cell3).group(1)
        self.assertIn(f'!= "{release}"', cell4)
        self.assertIn(f'_oscal_mapper_release = "{release}"', cell4)
        self.assertIn(f'!= "{release}"', cell5)
        self.assertIn(f'_oscal_mapper_release = "{release}"', cell5)
        self.assertIn(f'!= "{release}"', cell7)

if __name__ == "__main__":
    unittest.main()
