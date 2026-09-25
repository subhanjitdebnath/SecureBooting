#!/usr/bin/env python3
"""
Binary Security Header Generator (Build-Integration / CLI version)
--------------------------------------------------------------------
Non-interactive script intended to be called from a build system
(Makefile, post-build step, CI pipeline, IDE "post-build command", etc).

It takes as input (via command-line arguments, or a JSON config file):
  1. Validation type             -> sha256 / digital-signature / mac
  2. Path to raw application.bin -> folder + filename, or a full/absolute path
  3. Header start address        -> e.g. 0x08000000
  4. Application start address   -> e.g. 0x08008000
  5. Output file path            -> folder + filename, or a full/absolute path
                                     (defaults to out.bin in the current folder)

The SHA-256 digest of application.bin is computed automatically.

Builds a 41-byte header:

    Offset  Size  Field
    ------  ----  ---------------------------
    0       1     Validation type
    1       4     Application start address (uint32, little-endian)
    5       4     Application length in bytes (uint32, little-endian)
    9       32    SHA-256 digest (computed from application.bin)

...then assembles the final image as:

    [ header (41 bytes) ][ 0xFF padding ][ raw application binary ]

The padding fills the gap between the end of the header (at the header
start address) and the application start address, so the application
in the final image lands exactly at its configured start address.

Only "sha256" validation is implemented for now; the other two
validation types are stubbed out and will exit with a non-zero
status and a clear message if selected.

------------------------------------------------------------------
USAGE
------------------------------------------------------------------
Command-line arguments (full/absolute paths, or folder + filename):

    python generate_header.py \\
        --input "C:/builds/Debug/application.bin" \\
        --output "C:/builds/Debug/output/Application_Secure.bin" \\
        --header-addr 0x08000000 \\
        --app-addr 0x08008000 \\
        --validation-type sha256

Or via a JSON config file (useful for checking a config into the repo
alongside the build so every build uses the same addresses). "input_dir"
and "output_dir" are optional -- if given, they're combined with "input"
and "output"; if "input"/"output" are already full/absolute paths, the
"*_dir" fields are ignored for that one:

    python generate_header.py --config header_config.json

    # header_config.json:
    {
        "input_dir": "C:/builds/Debug",
        "input": "application.bin",
        "output_dir": "C:/builds/Debug/output",
        "output": "Application_Secure.bin",
        "header_addr": "0x08000000",
        "app_addr": "0x08008000",
        "validation_type": "sha256"
    }

    # Equivalently, full paths with no *_dir fields needed:
    {
        "input": "C:/builds/Debug/application.bin",
        "output": "C:/builds/Debug/output/Application_Secure.bin",
        "header_addr": "0x08000000",
        "app_addr": "0x08008000",
        "validation_type": "sha256"
    }

Command-line arguments override values from --config if both are given.
The output folder is created automatically if it doesn't already exist.

Exit codes (useful for failing a build step):
    0  success
    1  bad arguments / invalid config
    2  input file not found / unreadable
    3  address overlap or other validation error
    4  validation type not implemented
------------------------------------------------------------------
"""

import argparse
import hashlib
import json
import os
import struct
import sys

VALIDATION_TYPES = {
    "sha256": ("SHA-256 only", 0x01),
    "digital-signature": ("Digital Signature", 0x02),
    "mac": ("MAC Authentication", 0x03),
}

HEADER_FMT = "<B I I 32s"   # 1 + 4 + 4 + 32 = 41 bytes
HEADER_SIZE = struct.calcsize(HEADER_FMT)
DEFAULT_OUTPUT = "out.bin"
PAD_BYTE = b"\xFF"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_int(raw, field_name):
    """Accepts '0x08000000', '08000000' (hex) or a plain decimal string."""
    raw = str(raw).strip()
    try:
        return int(raw, 0) & 0xFFFFFFFF
    except ValueError:
        eprint(f"Error: invalid {field_name!r}: {raw!r}")
        sys.exit(1)


def compute_sha256(file_path):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.digest()


def build_header(validation_code, start_addr, length, digest):
    return struct.pack(HEADER_FMT, validation_code, start_addr, length, digest)


def resolve_path(directory, filename):
    """
    Combine an optional folder path with a filename.

    - If `filename` is already a full/absolute path, it's used as-is and
      `directory` is ignored.
    - If `directory` is given and `filename` is relative, they're joined.
    - If `directory` is not given, `filename` is used as-is (may be a
      relative path resolved against the current working directory, which
      is how the original --input/--output behaved).
    """
    filename = os.path.expanduser(str(filename))
    if os.path.isabs(filename):
        return filename
    if directory:
        return os.path.join(os.path.expanduser(str(directory)), filename)
    return filename


def load_config(config_path):
    if not os.path.isfile(config_path):
        eprint(f"Error: config file not found: {config_path}")
        sys.exit(1)
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        eprint(f"Error: invalid JSON in config file {config_path}: {e}")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a security header and assemble the final application binary "
                    "for use as an automated build step.",
    )
    parser.add_argument("--config", help="Path to a JSON config file with any of the options below.")
    parser.add_argument(
        "-i", "--input",
        help="Path to the raw application.bin file (full path, or filename to combine with --input-dir).",
    )
    parser.add_argument("--input-dir", help="Folder containing the input file (optional; combined with --input).")
    parser.add_argument(
        "-o", "--output",
        help=f"Output file path (full path, or filename to combine with --output-dir; default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument("--output-dir", help="Folder to write the output file into (optional; combined with --output).")
    parser.add_argument("--header-addr", help="Header start address, e.g. 0x08000000.")
    parser.add_argument("--app-addr", help="Application start address, e.g. 0x08008000.")
    parser.add_argument(
        "--validation-type",
        choices=list(VALIDATION_TYPES.keys()),
        help="Validation type (default: sha256).",
    )
    args = parser.parse_args()

    # Merge: config file provides defaults, CLI args override.
    merged = {}
    if args.config:
        merged.update(load_config(args.config))
    if args.input:
        merged["input"] = args.input
    if args.input_dir:
        merged["input_dir"] = args.input_dir
    if args.output:
        merged["output"] = args.output
    if args.output_dir:
        merged["output_dir"] = args.output_dir
    if args.header_addr:
        merged["header_addr"] = args.header_addr
    if args.app_addr:
        merged["app_addr"] = args.app_addr
    if args.validation_type:
        merged["validation_type"] = args.validation_type

    required = ["input", "header_addr", "app_addr"]
    missing = [k for k in required if k not in merged or merged[k] in (None, "")]
    if missing:
        eprint(f"Error: missing required option(s): {', '.join(missing)}")
        eprint("Provide them via --input/--header-addr/--app-addr or a --config file.")
        sys.exit(1)

    merged.setdefault("output", DEFAULT_OUTPUT)
    merged.setdefault("validation_type", "sha256")

    return merged


def main():
    cfg = parse_args()

    validation_key = cfg["validation_type"]
    if validation_key not in VALIDATION_TYPES:
        eprint(f"Error: unknown validation type {validation_key!r}. "
               f"Choices: {list(VALIDATION_TYPES.keys())}")
        sys.exit(1)
    name, code = VALIDATION_TYPES[validation_key]
    if validation_key != "sha256":
        eprint(f"Error: '{name}' is not implemented yet. Only 'sha256' is supported currently.")
        sys.exit(4)

    input_path = resolve_path(cfg.get("input_dir"), cfg["input"])
    output_path = resolve_path(cfg.get("output_dir"), cfg["output"])

    if not os.path.isfile(input_path):
        eprint(f"Error: input file not found: {input_path}")
        sys.exit(2)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    header_addr = parse_int(cfg["header_addr"], "header_addr")
    app_addr = parse_int(cfg["app_addr"], "app_addr")

    length = os.path.getsize(input_path)
    digest = compute_sha256(input_path)
    header = build_header(code, app_addr, length, digest)

    pad_len = app_addr - header_addr - HEADER_SIZE
    if pad_len < 0:
        eprint(
            f"Error: application start address (0x{app_addr:08X}) overlaps the header "
            f"(header occupies 0x{header_addr:08X}-0x{header_addr + HEADER_SIZE - 1:08X})."
        )
        sys.exit(3)

    with open(input_path, "rb") as f:
        app_data = f.read()

    final_binary = header + (PAD_BYTE * pad_len) + app_data

    with open(output_path, "wb") as f:
        f.write(final_binary)

    print(f"Validation type  : {name} (0x{code:02X})")
    print(f"Application file : {input_path}")
    print(f"Header address   : 0x{header_addr:08X}")
    print(f"App start address: 0x{app_addr:08X}")
    print(f"App length       : {length} bytes")
    print(f"SHA-256          : {digest.hex()}")
    print(f"Header size      : {HEADER_SIZE} bytes")
    print(f"Padding (0xFF)   : {pad_len} bytes")
    print(f"Final image size : {len(final_binary)} bytes")
    print(f"Output written to: {os.path.abspath(output_path)}")

    sys.exit(0)


if __name__ == "__main__":
    main()