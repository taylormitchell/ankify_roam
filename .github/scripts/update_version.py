import re
import os
import subprocess

CHANGELOG = "CHANGELOG.md"
VERSION_FILE = "ankify_roam/_version.py"

# Get new version from changelog
with open(CHANGELOG) as f:
    changelog = f.read()
pat_version="##\s*(\d+\.\d+\.\d+)"
res = re.search("(?##\s*)\d+\.\d+\.\d+", changelog)
if res:
    new_version = res.group()
else:
    raise ValueError("Couldn't find version in changelog")

# Confirm version number doesn't already exist
res = subprocess.run(["git", "tag"], capture_output=True)
existing_versions = res.stdout.decode().split()
if "v"+new_version in existing_versions:
    raise ValueError(f"New version {new_version} already exists")

# Get new version's changes
res = re.split("##\s*\d+\.\d+\.\d+.*", changelog)
changes = res[1].strip()

# Update version file
with open(VERSION_FILE, "w") as f:
    f.write(f"__version__ = '{new_version}'")

print(new_version)
