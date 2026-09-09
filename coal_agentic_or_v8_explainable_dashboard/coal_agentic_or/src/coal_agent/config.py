from pathlib import Path
import yaml


def load_config(path="config/network.yaml"):
    path = Path(path).resolve()
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Keep the project root so scheduled runs can locate persistent scenario inputs.
    cfg["_project_root"] = str(path.parent.parent)
    return cfg
