"""Print a reproducibility manifest for engineering experiment records."""
import json, platform
import importlib.metadata as md
packages=['fastapi','uvicorn','pydantic','numpy','scipy','pytest','scikit-learn','wfdb']
manifest={'python':platform.python_version(),'platform':platform.platform(),
          'libraries':{}}
for package in packages:
    try:manifest['libraries'][package]=md.version(package)
    except md.PackageNotFoundError:manifest['libraries'][package]='not installed'
print(json.dumps(manifest,indent=2))
