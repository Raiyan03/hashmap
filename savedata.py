import sys
import csv

SEPARATOR = "======================================================================"


def extract_block(text: str, header_prefix: str) -> str:
    """
    Find the block of text that belongs to a given experiment.

    It looks for a line containing header_prefix (e.g., "EXPERIMENT 1"),
    then skips the separator line right after it, and collects everything
    until the next separator.
    """
    lines = text.splitlines()
    in_section = False
    sep_seen_after_header = False
    collected = []

    header_prefix_lower = header_prefix.lower()

    for line in lines:
        if not in_section:
            # Look for the experiment header line
            if header_prefix_lower in line.lower():
                in_section = True
                sep_seen_after_header = False
            continue
        else:
            # We are inside this experiment's region
            if SEPARATOR in line:
                if not sep_seen_after_header:
                    # This is the separator immediately after the header -> skip it
                    sep_seen_after_header = True
                    continue
                else:
                    # Second separator -> end of this experiment block
                    break
            collected.append(line)

    return "\n".join(collected)


def parse_csv_like_block(block: str, ignore_hash_lines: bool = False):
    """
    Turn lines that look like CSV (contain commas)
    into (header, rows).

    Returns:
        header: list[str] | None
        rows: list[list[str]] | None
    """
    block = block.strip()
    if not block:
        return None, None

    lines = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if ignore_hash_lines and line.startswith("#"):
            continue
        if "," in line:
            lines.append(line)

    if not lines:
        return None, None

    # First CSV-looking line is header
    header_line = lines[0]
    header = [h.strip() for h in header_line.split(",")]

    rows = []
    for data_line in lines[1:]:
        parts = [p.strip() for p in data_line.split(",")]
        rows.append(parts)

    return header, rows


def main():
    if len(sys.argv) < 2:
        print("Usage: python savedata.py <hashOutputFile.txt>")
        return

    input_path = sys.argv[1]

    with open(input_path, "r") as f:
        text = f.read()

    # ------------ Experiment 1 ------------
    exp1_block = extract_block(text, "EXPERIMENT 1")
    h1, rows1 = parse_csv_like_block(exp1_block)
    if h1 is not None and rows1 is not None:
        out1 = f"experiment1_{input_path.replace('.txt', '')}.csv"
        with open(out1, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(h1)
            writer.writerows(rows1)
        print(f"Wrote {out1}")
    else:
        print("No data found for Experiment 1")

    # ------------ Experiment 2 ------------
    exp2_block = extract_block(text, "EXPERIMENT 2")
    h2, rows2 = parse_csv_like_block(exp2_block)
    if h2 is not None and rows2 is not None:
        out2 = f"experiment2_{input_path.replace('.txt', '')}.csv"
        with open(out2, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(h2)
            writer.writerows(rows2)
        print(f"Wrote {out2}")
    else:
        print("No data found for Experiment 2")

    # ------------ Experiment 3 ------------
    exp3_block = extract_block(text, "EXPERIMENT 3")
    h3, rows3 = parse_csv_like_block(exp3_block)
    if h3 is not None and rows3 is not None:
        out3 = f"experiment3_{input_path.replace('.txt', '')}.csv"
        with open(out3, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(h3)
            writer.writerows(rows3)
        print(f"Wrote {out3}")
    else:
        print("No data found for Experiment 3")

    # ------------ Experiment 4 ------------
    exp4_block = extract_block(text, "EXPERIMENT 4")
    h4, rows4 = parse_csv_like_block(exp4_block, ignore_hash_lines=True)
    if h4 is not None and rows4 is not None:
        out4 = f"experiment4_{input_path.replace('.txt', '')}.csv"
        with open(out4, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(h4)
            writer.writerows(rows4)
        print(f"Wrote {out4}")
    else:
        print("No data found for Experiment 4")


if __name__ == "__main__":
    main()
