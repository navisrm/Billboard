import re
from pathlib import Path

# Personal content, kept out of git (see .gitignore) and copied to the Pi by `make deploy`.
PLAN_FILE = Path(__file__).parent / "daily_plan.md"


def get_plan():
    """Parse daily_plan.md into title, steps, checklist and the closing note. None if the file is absent."""
    try:
        text = PLAN_FILE.read_text()
    except OSError:
        return None

    plan = {"title": "", "steps": [], "checklist": [], "important": ""}
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("# "):
            plan["title"] = line[2:]
        elif line.startswith("## "):
            heading = line[3:]
            step = re.match(r"Step \d+:\s*(.*)", heading)
            if step:
                section = {"title": step.group(1), "bullets": []}
                plan["steps"].append(section)
            else:
                section = heading.lower()
        elif line.startswith("- ") and isinstance(section, dict):
            section["bullets"].append(line[2:])
        elif line.startswith("|") and section == "daily checklist":
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            # Skip the header row and the |---|---| separator.
            if cells[0] != "Activity" and not set(cells[0]) <= set("-: "):
                plan["checklist"].append(cells)
        elif line and section == "important":
            plan["important"] = f"{plan['important']} {line}".strip()
    return plan
