#!/usr/bin/env python3
"""Render Homebrew and AUR metadata from a published Mailghost release."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPOSITORY = "Kelvin-Jesus/mailghost"
TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")
CHECKSUM_PATTERN = re.compile(
    r"^(?P<checksum>[0-9a-f]{64})  (?P<filename>[A-Za-z0-9._+-]+)$"
)
PLATFORMS = {
    "macos-aarch64": "macOS ARM64",
    "macos-x86_64": "macOS x86_64",
    "linux-aarch64": "Linux ARM64",
    "linux-x86_64": "Linux x86_64",
}


class MetadataError(ValueError):
    """Raised when release metadata cannot safely produce package definitions."""


def parse_tag(tag: str) -> str:
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise MetadataError(f"tag must be a stable semantic version such as v1.2.3: {tag}")
    return match.group("version")


def parse_checksums(contents: str) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line_number, line in enumerate(contents.splitlines(), start=1):
        if not line:
            continue
        match = CHECKSUM_PATTERN.fullmatch(line)
        if match is None:
            raise MetadataError(f"malformed checksum line {line_number}: {line!r}")
        filename = match.group("filename")
        if filename in checksums:
            raise MetadataError(f"duplicate checksum entry: {filename}")
        checksums[filename] = match.group("checksum")
    return checksums


def required_checksums(tag: str, checksums: dict[str, str]) -> dict[str, str]:
    required = {
        platform: f"mailghost-{tag}-{platform}.tar.gz" for platform in PLATFORMS
    }
    missing = [filename for filename in required.values() if filename not in checksums]
    if missing:
        raise MetadataError(f"missing release checksums: {', '.join(sorted(missing))}")
    return {platform: checksums[filename] for platform, filename in required.items()}


def release_url(tag: str, platform: str) -> str:
    filename = f"mailghost-{tag}-{platform}.tar.gz"
    return f"https://github.com/{REPOSITORY}/releases/download/{tag}/{filename}"


def render_homebrew(tag: str, version: str, checksums: dict[str, str]) -> str:
    def source(platform: str, indentation: str = "      ") -> str:
        return (
            f'{indentation}url "{release_url(tag, platform)}"\n'
            f'{indentation}sha256 "{checksums[platform]}"'
        )

    return f'''class Mailghost < Formula
  desc "Friendly disposable Mail.tm inbox for your terminal"
  homepage "https://github.com/{REPOSITORY}"
  version "{version}"
  license "MIT"

  on_macos do
    on_arm do
{source("macos-aarch64")}
    end
    on_intel do
{source("macos-x86_64")}
    end
  end

  on_linux do
    on_arm do
{source("linux-aarch64")}
    end
    on_intel do
{source("linux-x86_64")}
    end
  end

  def install
    bin.install "mailghost"
    doc.install "README.md"
    pkgshare.install "LICENSE"
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/mailghost --version")
  end
end
'''


def render_pkgbuild(tag: str, version: str, checksums: dict[str, str]) -> str:
    return f'''# Maintainer: Kelvin Jesus <kj.avelino.cambiaghi@gmail.com>
pkgname=mailghost-bin
pkgver={version}
pkgrel=1
pkgdesc='Friendly disposable Mail.tm inbox for your terminal'
arch=('x86_64' 'aarch64')
url='https://github.com/{REPOSITORY}'
license=('MIT')
depends=('gcc-libs' 'glibc' 'openssl')
provides=("mailghost=${{pkgver}}")
conflicts=('mailghost')
source_x86_64=("mailghost-${{pkgver}}-x86_64.tar.gz::{release_url(tag, "linux-x86_64")}")
sha256sums_x86_64=('{checksums["linux-x86_64"]}')
source_aarch64=("mailghost-${{pkgver}}-aarch64.tar.gz::{release_url(tag, "linux-aarch64")}")
sha256sums_aarch64=('{checksums["linux-aarch64"]}')

package() {{
  install -Dm755 mailghost "${{pkgdir}}/usr/bin/mailghost"
  install -Dm644 LICENSE "${{pkgdir}}/usr/share/licenses/${{pkgname}}/LICENSE"
  install -Dm644 README.md "${{pkgdir}}/usr/share/doc/${{pkgname}}/README.md"
}}
'''


def render(tag: str, checksum_file: Path, output_directory: Path) -> None:
    version = parse_tag(tag)
    parsed = parse_checksums(checksum_file.read_text(encoding="utf-8"))
    checksums = required_checksums(tag, parsed)

    formula_directory = output_directory / "homebrew" / "Formula"
    aur_directory = output_directory / "aur"
    formula_directory.mkdir(parents=True, exist_ok=True)
    aur_directory.mkdir(parents=True, exist_ok=True)

    (formula_directory / "mailghost.rb").write_text(
        render_homebrew(tag, version, checksums), encoding="utf-8"
    )
    (aur_directory / "PKGBUILD").write_text(
        render_pkgbuild(tag, version, checksums), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--checksums", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        render(arguments.tag, arguments.checksums, arguments.output)
    except (MetadataError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
