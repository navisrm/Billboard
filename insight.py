from pathlib import Path

# Personal content, kept out of git (see .gitignore) and copied to the Pi by `make deploy`.
INSIGHT_FILE = Path(__file__).parent / "insight.md"


def get_insight():
    """Parse insight.md into a title, intro paragraphs and sections. None if the file is absent.

    Format: "# Title", then intro paragraphs, then "## Heading" sections with paragraphs and "- " bullets.
    A bullet written as "**Label:** text" is shown as a card with that label.
    """
    try:
        text = INSIGHT_FILE.read_text()
    except OSError:
        return None

    insight = {"title": "", "intro": [], "sections": []}
    paragraphs = insight["intro"]
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            insight["title"] = line[2:]
        elif line.startswith("## "):
            section = {"heading": line[3:], "paragraphs": [], "bullets": []}
            insight["sections"].append(section)
            paragraphs = section["paragraphs"]
        elif line.startswith("- ") and section:
            body = line[2:]
            label = ""
            if body.startswith("**") and ":**" in body:
                label, body = body[2:].split(":**", 1)
            section["bullets"].append({"label": label, "text": body.strip()})
        else:
            paragraphs.append(line)
    return insight
