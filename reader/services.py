from pathlib import Path
from hashlib import sha1

import fitz
from django.core.files.base import ContentFile

from .models import EditionPage


def pdf_digest(pdf_path):
    digest = sha1()
    with pdf_path.open("rb") as pdf_file:
        for chunk in iter(lambda: pdf_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def convert_pdf_to_pages(edition, zoom=2):
    edition.pages.all().delete()

    pdf_path = Path(edition.pdf.path)
    version = pdf_digest(pdf_path)
    document = fitz.open(pdf_path)
    matrix = fitz.Matrix(zoom, zoom)

    try:
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_name = f"edition-{edition.pk}-{version}-page-{index:02d}.png"
            page_image = ContentFile(pixmap.tobytes("png"), name=image_name)
            EditionPage.objects.create(
                edition=edition,
                number=index,
                image=page_image,
            )
    finally:
        document.close()

    return edition.pages.count()
