import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Path to the input PDF
input_pdf_path = "test_file.pdf"
output_pdf_path = "novel_extracted.pdf"

# Set up file
packet = io.BytesIO()
can = canvas.Canvas(packet, pagesize=letter)
y_position = 750  # Starting y-position for text

with pdfplumber.open(input_pdf_path) as pdf:
    for page in pdf.pages:
        page_words = page.extract_words(extra_attrs=["size"])
        sorted_words = sorted(page_words, key=lambda x: (x['top'], x['x0']))
        title = ''

        for obj in sorted_words:
            text = obj['text']
            font_size = obj['size']
            if 21 <= font_size <= 23:
                title += text + " "
        if (title):
            title = 'Chapter ' + title.strip()
            print(title)

# Function to extract text and write to PDF
def extract_text_to_pdf(pdf_path, output_path):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    y_position = 750  # Starting y-position for text
    chapter_count = 0
    paragraph_buffer = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_words = page.extract_words(extra_attrs=["size"])
            sorted_words = sorted(page_words, key=lambda x: (x['top'], x['x0']))
            first_letter_buffer = ""

            for obj in sorted_words:
                text = obj['text']
                font_size = obj['size']
                # Chapter title (~22)
                if 21 <= font_size <= 23:
                    # Write any remaining paragraph buffer
                    if paragraph_buffer:
                        can.setFont("Helvetica", 12)
                        can.drawString(72, y_position, paragraph_buffer.strip())
                        y_position -= 18
                        paragraph_buffer = ""
                    chapter_count += 1
                    chapter_title = f"{chapter_count} - {text.upper()}"
                    can.setFont("Helvetica-Bold", 16)
                    can.drawString(72, y_position, chapter_title)
                    y_position -= 30
                # Stylized first letter (~72) after chapter title
                elif 70 <= font_size <= 74:
                    first_letter_buffer = text
                # Body text (~15)
                elif 14 <= font_size <= 16:
                    word = f"{first_letter_buffer}{text}" if first_letter_buffer else text
                    paragraph_buffer += f" {word}"
                    first_letter_buffer = ""

            # Write the buffered paragraph at the end of the page
            if paragraph_buffer:
                can.setFont("Helvetica", 12)
                can.drawString(72, y_position, paragraph_buffer.strip())
                y_position -= 18
                paragraph_buffer = ""

            if y_position < 72:
                can.showPage()
                y_position = 750

    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)
    writer = PdfWriter()
    for page in new_pdf.pages:
        writer.add_page(page)
    with open(output_path, "wb") as out_pdf:
        writer.write(out_pdf)
    print(f"Extracted text saved to {output_path}")

# Run extraction
# extract_text_to_pdf(input_pdf_path, output_pdf_path)
