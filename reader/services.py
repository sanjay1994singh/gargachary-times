from pathlib import Path

import fitz
from django.core.files.base import ContentFile

from .models import EditionPage


def convert_pdf_to_pages(edition, zoom=2):
    edition.pages.all().delete()

    pdf_path = Path(edition.pdf.path)
    document = fitz.open(pdf_path)
    matrix = fitz.Matrix(zoom, zoom)

    try:
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_name = f"edition-{edition.pk}-page-{index:02d}.png"
            page_image = ContentFile(pixmap.tobytes("png"), name=image_name)
            EditionPage.objects.create(
                edition=edition,
                number=index,
                image=page_image,
            )
    finally:
        document.close()

    return edition.pages.count()
