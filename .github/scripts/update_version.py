import re
import os
import subprocess

CHANGELOG = "CHANGELOG.md"
VERSION_FILE = "ankify_roam/_version.py"

# Get new version from changelog
with open(CHANGELOG) as f:
    changelog = f.read()
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

# Update version file
with open(VERSION_FILE, "w") as f:
    f.write(f"__version__ = '{new_version}'")

print(new_version)
