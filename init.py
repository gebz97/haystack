#!/usr/bin/env python3
import subprocess
import os
import venv

VENV_DIR = "v"
REQUIREMENTS = "requirements.txt"


def get_venv_python(venv_dir):
    for candidate in ["python", "python3"]:
        for bin_dir in ["Scripts", "bin"]:
            path = os.path.join(venv_dir, bin_dir, candidate)
            if os.path.isfile(path) or os.path.isfile(path + ".exe"):
                return path
    raise RuntimeError(f"Could not find Python in venv {venv_dir}")


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, **kwargs)


# Create venv if it doesn't exist
if not os.path.isdir(VENV_DIR):
    print(f"Creating venv in ./{VENV_DIR}...")
    venv.create(VENV_DIR, with_pip=True)
else:
    print(f"Venv ./{VENV_DIR} already exists, skipping.")

python = get_venv_python(VENV_DIR)

run([python, "-m", "pip", "install", "--upgrade", "pip", "-q"])

if os.path.isfile(REQUIREMENTS):
    print(f"Installing requirements from {REQUIREMENTS}...")
    run([python, "-m", "pip", "install", "-r", REQUIREMENTS])
else:
    print(f"No {REQUIREMENTS} found, skipping.")

print("Done.")
