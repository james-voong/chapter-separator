import os
import re
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    # Replace invalid path characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(" .")
    return name or "chapter"


def is_blank_page(page) -> bool:
    """Return True if the page has no meaningful text content."""
    text = page.extract_text()
    return text is None or not text.strip()


def get_chapter_starts(pdf) -> list[tuple[int, str]]:
    """
    Scan PDF and return list of (page_index_0based, chapter_name) for each chapter.
    Chapters are detected by large font (21-23pt) lines matching "N - Title".
    """
    chapters = []
    for page_idx, page in enumerate(pdf.pages):
        page_words = page.extract_words(extra_attrs=["size"])
        if not page_words:
            continue
        sorted_words = sorted(page_words, key=lambda x: (x["top"], x["x0"]))
        # Collect first "line" of large-font words (same approximate top)
        line_words = []
        first_top = None
        for obj in sorted_words:
            font_size = obj.get("size")
            if font_size is None or not (21 <= font_size <= 23):
                continue
            top = obj["top"]
            if first_top is None:
                first_top = top
            if abs(top - first_top) > 8:  # New line
                break
            line_words.append(obj["text"])
        if not line_words:
            continue
        line_text = " ".join(line_words)
        # Match "1 - Reincarnation" or "2 - A.I. Chip"
        m = re.match(r"^(\d+)\s*-\s*(.+)$", line_text.strip())
        if m:
            chapter_name = m.group(2).strip()
            chapters.append((page_idx, chapter_name))
    return chapters


def split_pdf_by_chapters(
    input_pdf_path: str,
    output_dir: str | Path,
    *,
    output_prefix: str = "",
) -> list[str]:
    """
    Split a combined PDF into one file per chapter.
    - Chapter boundaries: lines like "1 - Reincarnation", "2 - A.I. Chip".
    - Each output file is named after the chapter (sanitized), optional prefix.
    - Leading and trailing blank pages are removed from each chapter.
    - Each chapter starts at the start of a page (no mid-page splits).
    Returns list of output file paths.
    """
    input_path = Path(input_pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(input_pdf_path)
    num_pages = len(reader.pages)

    with pdfplumber.open(input_pdf_path) as pdf:
        chapter_starts = get_chapter_starts(pdf)
        if not chapter_starts:
            raise ValueError("No chapters found (no 'N - Title' lines with large font).")

        output_paths = []
        for i, (start_page_idx, chapter_name) in enumerate(chapter_starts):
            end_page_idx = (
                chapter_starts[i + 1][0] - 1
                if i + 1 < len(chapter_starts)
                else num_pages - 1
            )
            if end_page_idx < start_page_idx:
                continue

            # Trim leading blank pages
            first = start_page_idx
            while first <= end_page_idx and is_blank_page(pdf.pages[first]):
                first += 1
            # Trim trailing blank pages
            last = end_page_idx
            while last >= first and is_blank_page(pdf.pages[last]):
                last -= 1

            if first > last:
                continue  # Chapter was all blank

            writer = PdfWriter()
            for p in range(first, last + 1):
                writer.add_page(reader.pages[p])

            safe_name = sanitize_filename(chapter_name)
            chapter_num = i + 1
            out_path = output_dir / f"{output_prefix}{chapter_num:04d} - {safe_name}.pdf"
            with open(out_path, "wb") as f:
                writer.write(f)
            output_paths.append(str(out_path))
            print(f"  {out_path.name} (pages {first + 1}–{last + 1})")

        return output_paths


DATA_DIR = os.environ.get("DATA_DIR", "data")
CHAPTERS_DIR = os.environ.get("CHAPTERS_DIR", "chapters")

if __name__ == "__main__":
    data_path = Path(DATA_DIR)
    chapters_path = Path(CHAPTERS_DIR)
    if not data_path.is_dir():
        raise SystemExit(f"Data directory not found: {data_path}")

    pdf_files = sorted(data_path.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDF files found in {data_path}")

    total = 0
    for pdf_path in pdf_files:
        print(f"Splitting: {pdf_path.name}")
        try:
            paths = split_pdf_by_chapters(str(pdf_path), chapters_path)
            total += len(paths)
        except ValueError as e:
            print(f"  Skipped: {e}")
    print(f"Created {total} chapter PDF(s) in {chapters_path}/")
