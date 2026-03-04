import os
import re
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from pathlib import Path

_RE_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*]')
_RE_CHAPTER_HEADING = re.compile(r"^(\d+)\s*-\s*(.+)$")


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    name = _RE_UNSAFE_FILENAME.sub("_", name)
    name = name.strip(" .")
    return name or "chapter"


def is_blank_page(page) -> bool:
    """Return True if the page has no meaningful text content."""
    text = page.extract_text()
    return text is None or not text.strip()


def get_chapter_starts(pdf) -> list[tuple[int, int, str]]:
    """
    Scan PDF and return list of (page_index_0based, chapter_number, chapter_name) for each chapter.
    Chapters are detected by large font (21-23pt) lines matching "N - Title".
    """
    chapters = []
    for page_idx, page in enumerate(pdf.pages):
        page_words = page.extract_words(extra_attrs=["size"])
        if not page_words:
            continue
        sorted_words = sorted(page_words, key=lambda x: (x["top"], x["x0"]))
        large_words = [w for w in sorted_words if (s := w.get("size")) is not None and 21 <= s <= 23]
        if not large_words:
            continue
        line_words = []
        first_top = None
        for obj in large_words:
            top = obj["top"]
            if first_top is None:
                first_top = top
            if abs(top - first_top) > 8:
                break
            line_words.append(obj["text"])
        if not line_words:
            continue
        m = _RE_CHAPTER_HEADING.match(" ".join(line_words).strip())
        if m:
            chapter_num = int(m.group(1))
            chapter_name = m.group(2).strip()
            chapters.append((page_idx, chapter_num, chapter_name))
    return chapters


def split_pdf_by_chapters(input_pdf_path: str, output_dir: str | Path) -> list[str]:
    """
    Split a combined PDF into one file per chapter. Detects "N - Title" lines in
    large font; strips leading/trailing blank pages. Returns output file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(input_pdf_path)
    num_pages = len(reader.pages)

    with pdfplumber.open(input_pdf_path) as pdf:
        chapter_starts = get_chapter_starts(pdf)
        if not chapter_starts:
            raise ValueError("No chapters found (no 'N - Title' lines with large font).")

        output_paths = []
        for i, (start_page_idx, chapter_num, chapter_name) in enumerate(chapter_starts):
            end_page_idx = (
                chapter_starts[i + 1][0] - 1
                if i + 1 < len(chapter_starts)
                else num_pages - 1
            )
            if end_page_idx < start_page_idx:
                continue

            first = start_page_idx
            while first <= end_page_idx and is_blank_page(pdf.pages[first]):
                first += 1
            last = end_page_idx
            while last >= first and is_blank_page(pdf.pages[last]):
                last -= 1

            if first > last:
                continue

            writer = PdfWriter()
            for p in range(first, last + 1):
                writer.add_page(reader.pages[p])

            safe_name = sanitize_filename(chapter_name)
            pad_width = max(4, len(str(chapter_num)))
            out_path = output_dir / f"{chapter_num:0{pad_width}d} - {safe_name}.pdf"
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
