import tempfile
import unittest
from pathlib import Path

from render_packages import (
    MetadataError,
    parse_checksums,
    parse_tag,
    render,
    required_checksums,
)


TAG = "v1.2.3"
REQUIRED_FILENAMES = [
    f"mailghost-{TAG}-macos-aarch64.tar.gz",
    f"mailghost-{TAG}-macos-x86_64.tar.gz",
    f"mailghost-{TAG}-linux-aarch64.tar.gz",
    f"mailghost-{TAG}-linux-x86_64.tar.gz",
]


def checksum_file_contents() -> str:
    return "\n".join(
        f"{index:064x}  {filename}"
        for index, filename in enumerate(REQUIRED_FILENAMES, start=1)
    )


class RenderPackagesTests(unittest.TestCase):
    def test_parse_tag_accepts_stable_semantic_version(self) -> None:
        self.assertEqual(parse_tag(TAG), "1.2.3")

    def test_parse_tag_rejects_non_release_tag(self) -> None:
        with self.assertRaisesRegex(MetadataError, "stable semantic version"):
            parse_tag("latest")

    def test_parse_checksums_rejects_malformed_line(self) -> None:
        with self.assertRaisesRegex(MetadataError, "malformed checksum line"):
            parse_checksums("not-a-checksum")

    def test_parse_checksums_rejects_duplicate_filename(self) -> None:
        line = f"{'a' * 64}  mailghost-{TAG}-linux-x86_64.tar.gz"
        with self.assertRaisesRegex(MetadataError, "duplicate checksum entry"):
            parse_checksums(f"{line}\n{line}\n")

    def test_required_checksums_rejects_missing_platform(self) -> None:
        parsed = parse_checksums(checksum_file_contents())
        parsed.pop(REQUIRED_FILENAMES[0])
        with self.assertRaisesRegex(MetadataError, "missing release checksums"):
            required_checksums(TAG, parsed)

    def test_render_writes_formula_and_pkgbuild(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            checksum_file = root / "SHA256SUMS"
            checksum_file.write_text(checksum_file_contents(), encoding="utf-8")

            render(TAG, checksum_file, root / "generated")

            formula = (root / "generated/homebrew/Formula/mailghost.rb").read_text()
            pkgbuild = (root / "generated/aur/PKGBUILD").read_text()
            self.assertIn('version "1.2.3"', formula)
            self.assertIn("mailghost-v1.2.3-macos-aarch64.tar.gz", formula)
            self.assertIn("pkgname=mailghost-bin", pkgbuild)
            self.assertIn("provides=(\"mailghost=${pkgver}\")", pkgbuild)


if __name__ == "__main__":
    unittest.main()
