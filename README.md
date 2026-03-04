# Chapter Separator

Splits multi-chapter PDFs into one PDF per chapter. Place combined PDFs in `data/`; the script detects chapter boundaries and writes separate files into `chapters/`, with leading and trailing blank pages removed.

## How it works

- **Chapter detection:** Looks for lines in large font (21–23 pt) that match the pattern `N - Title` (e.g. `1 - Reincarnation`, `2 - A.I. Chip`). Each such line starts a new chapter on that page.
- **Output:** One PDF per chapter. Filenames are `0001 - Chapter Name.pdf`, `0002 - Chapter Name.pdf`, etc. (4-digit number + chapter title).
- **Cleanup:** Blank pages at the start and end of each chapter are dropped. Every chapter begins on a full page.

## Directory layout

```
data/        ← Put your combined PDF(s) here
chapters/    ← Separated chapter PDFs are written here
```

## Run locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Put your PDF(s) in `data/`.

3. Run:

   ```bash
   python chapter_separator.py
   ```

Output appears in `chapters/`. You can override paths with env vars:

- `DATA_DIR` — directory to read PDFs from (default: `data`)
- `CHAPTERS_DIR` — directory to write chapter PDFs to (default: `chapters`)

## Run with Docker

1. Build the image:

   ```bash
   docker build -t chapter-separator .
   ```

2. Run with a volume that contains `data/` (and optionally `chapters/`). From the project root:

   ```bash
   docker run --rm -v "$(pwd)":/data chapter-separator
   ```

   The container reads PDFs from `./data/` and writes chapter PDFs to `./chapters/`.

   To use another directory on the host:

   ```bash
   docker run --rm -v /path/to/folder:/data chapter-separator
   ```

   That folder must have a `data/` subfolder with your PDFs; `chapters/` will be created there for output.

## Requirements

- Python 3.x with `pdfplumber` and `PyPDF2` (see `requirements.txt`).
- PDFs whose chapter titles are in large font and match `N - Title` on a line by themselves.
