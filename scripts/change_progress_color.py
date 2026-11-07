#!/usr/bin/env python3
"""Patch a locally installed JDownloader JAR; no third-party dependencies."""
import argparse
import datetime
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

CLASS_NAME = "org/appwork/swing/exttable/renderercomponents/RendererProgressBar.class"
STOCK_SHA256 = "5349156548fdda69ddbd96c2111f47ca0a3b3d6a9e3727eac18f430b6244a320"
PATCHED_SHA256 = "9714f0f5b46f48a54a6abc00ca0eadbaa7a517101365b998c755a714dd1e6d7c"
# Binary delta for one verified JDownloader renderer version. No JDownloader JAR is bundled.
DELTA = [(9, 10, '4a'), (828, 828, '01000d676574466f726567726f756e6401001228294c6a6176612f6177742f436f6c6f723b01000e6a6176612f6177742f436f6c6f720700450100062849494929560c001100470a00460048'), (871, 872, '0d'), (1750, 1750, '430044000100130000001d0005000100000011bb0046591100641100b51100f6b70049b000000000000100')]
# RGB values in the new getForeground() method (three SIPUSH operands).
RGB_MARKER = bytes.fromhex("bb0046591100641100b51100f6b70049b0")


def convert_stock(data):
    if hashlib.sha256(data).hexdigest() != STOCK_SHA256:
        raise ValueError("Unsupported stock renderer class version; no changes made.")
    for start, end, replacement in reversed(DELTA):
        data = data[:start] + bytes.fromhex(replacement) + data[end:]
    if hashlib.sha256(data).hexdigest() != PATCHED_SHA256:
        raise ValueError("Binary patch verification failed; no changes made.")
    return data


def normalize_patched(data):
    """Verify a patched class matches the tested template except RGB operands."""
    marker = bytes.fromhex("bb00465911")
    start = data.find(marker)
    if len(data) != 1876 or start < 0 or data.find(marker, start + 1) >= 0:
        return False
    normalized = bytearray(data)
    for offset, value in zip((start + 5, start + 8, start + 11), (100, 181, 246)):
        normalized[offset:offset + 2] = value.to_bytes(2, "big")
    return hashlib.sha256(normalized).hexdigest() == PATCHED_SHA256


def recolor(data, hex_color):
    marker = bytes.fromhex("bb00465911")
    # Match the method bytecode, not an arbitrary RGB occurrence elsewhere in the class.
    start = data.find(marker)
    if start < 0 or data.find(marker, start + 1) >= 0:
        raise ValueError("Expected patched getForeground() method not found uniquely.")
    if data[start:start + 17] != RGB_MARKER and not (
        data[start:start + 5] == bytes.fromhex("bb00465911")
        and data[start + 7:start + 8] == b"\x11"
        and data[start + 10:start + 11] == b"\x11"
        and data[start + 13:start + 17] == bytes.fromhex("b70049b0")
    ):
        raise ValueError("Unexpected getForeground() bytecode; no changes made.")
    result = bytearray(data)
    rgb = bytes.fromhex(hex_color)
    for offset, value in zip((start + 5, start + 8, start + 11), rgb):
        result[offset:offset + 2] = value.to_bytes(2, "big")
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description="Change JDownloader download progress bar fill color")
    parser.add_argument("--color", required=True, help="Six-digit HEX, e.g. '#64B5F6'")
    parser.add_argument("--jd-dir", default=r"C:\Program Files\JDownloader", help="JDownloader installation directory")
    args = parser.parse_args()
    color = args.color.lstrip("#")
    if len(color) != 6 or any(c not in "0123456789abcdefABCDEF" for c in color):
        parser.error("--color must be a six-digit HEX RGB color")
    jar = Path(args.jd_dir) / "JDownloader.jar"
    if not jar.is_file():
        parser.error(f"JAR not found: {jar}; specify --jd-dir")
    try:
        with zipfile.ZipFile(jar) as archive:
            info = archive.getinfo(CLASS_NAME)
            current = archive.read(info)
            digest = hashlib.sha256(current).hexdigest()
            if digest == STOCK_SHA256:
                current = convert_stock(current)
                status = "Patched stock renderer"
            elif normalize_patched(current):
                # Validate exact bytecode structure before allowing a recolor.
                status = "Recolored existing patched renderer"
            else:
                raise ValueError("Unsupported JDownloader renderer version; no changes made.")
            updated = recolor(current, color)
            # Preserve every other JAR entry, including its metadata and compression settings.
            fd, tempname = tempfile.mkstemp(prefix="jd-progress-", suffix=".jar", dir=jar.parent)
            os.close(fd)
            temp = Path(tempname)
            try:
                with zipfile.ZipFile(temp, "w") as output:
                    for entry in archive.infolist():
                        output.writestr(entry, updated if entry.filename == CLASS_NAME else archive.read(entry.filename))
            except Exception:
                temp.unlink(missing_ok=True)
                raise
        # Validate the entire replacement before modifying the user's JAR.
        try:
            with zipfile.ZipFile(temp) as check:
                if check.testzip() is not None or check.read(CLASS_NAME) != updated:
                    raise ValueError("Patched JAR verification failed")
            backup = jar.with_name(jar.name + ".backup-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
            shutil.copy2(jar, backup)
            try:
                os.replace(temp, jar)
            except Exception:
                shutil.copy2(backup, jar)
                raise
        finally:
            temp.unlink(missing_ok=True)
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"{status}. Color: #{color.upper()}")
    print(f"Backup: {backup}")
    print("Restart JDownloader to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
