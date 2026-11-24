from pathlib import Path

QUOTES_FILE = Path(__file__).parent / "quotes.md"


def get_quotes():
    """Parse quotes.md: "# Author", then a table of "| # | Quote | Lesson |" rows. None if the file is absent."""
    try:
        text = QUOTES_FILE.read_text()
    except OSError:
        return None

    result = {"author": "", "quotes": []}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("# "):
            result["author"] = line[2:]
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            # Skip the header row and the |---|---| separator.
            if len(cells) < 3 or not cells[0].isdigit():
                continue
            result["quotes"].append({"text": cells[1].strip("“”\""), "lesson": cells[2]})
    return result if result["quotes"] else None
