from io import BytesIO
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse

from .forms import EditionUploadForm
from .models import Edition
from .services import convert_pdf_to_pages


SHARE_IMAGE_WIDTH = 1200
SHARE_IMAGE_HEIGHT = 630


def public_absolute_url(request, path):
    if not path:
        return ""

    parsed = urlparse(path)
    if parsed.scheme and parsed.netloc:
        return path

    site_url = getattr(settings, "SITE_URL", "").strip().rstrip("/")
    if site_url and "localhost" not in site_url and "127.0.0.1" not in site_url:
        return urljoin(f"{site_url}/", path.lstrip("/"))

    return request.build_absolute_uri(path)


def get_share_image_url(page):
    if not page or not page.image:
        return ""

    share_path = f"editions/share/edition-{page.edition_id}-page-{page.number:02d}.jpg"
    if default_storage.exists(share_path):
        return default_storage.url(share_path)

    try:
        from PIL import Image

        with default_storage.open(page.image.name, "rb") as image_file:
            image = Image.open(image_file).convert("RGB")

            resampling_filter = getattr(
                getattr(Image, "Resampling", Image),
                "LANCZOS",
            )
            ratio = SHARE_IMAGE_WIDTH / image.width
            resized_height = max(1, round(image.height * ratio))
            image = image.resize(
                (SHARE_IMAGE_WIDTH, resized_height),
                resampling_filter,
            )

            if resized_height >= SHARE_IMAGE_HEIGHT:
                image = image.crop((0, 0, SHARE_IMAGE_WIDTH, SHARE_IMAGE_HEIGHT))
            else:
                canvas = Image.new("RGB", (SHARE_IMAGE_WIDTH, SHARE_IMAGE_HEIGHT), "white")
                offset_y = (SHARE_IMAGE_HEIGHT - resized_height) // 2
                canvas.paste(image, (0, offset_y))
                image = canvas

            output = BytesIO()
            image.save(output, format="JPEG", quality=82, optimize=True)
            default_storage.save(share_path, ContentFile(output.getvalue()))
            return default_storage.url(share_path)
    except Exception:
        return page.image.url


def reader_home(request, pk=None):
    edition = get_object_or_404(Edition, pk=pk) if pk else Edition.objects.first()
    edition_list = Edition.objects.all()
    page_records = []
    editions_meta = [
        {
            "id": item.pk,
            "city": item.city,
            "section": item.section,
            "date": item.publish_date.isoformat(),
            "url": reverse("reader:edition", kwargs={"pk": item.pk}),
        }
        for item in edition_list
    ]

    if edition:
        page_records = list(edition.pages.all())
        pages = [
            {
                "number": page.number,
                "title": f"Page {page.number:02d}",
                "section": edition.section,
                "image": page.image.url,
            }
            for page in page_records
        ]
        editions = [item.city for item in edition_list]
        sections = sorted({item.section for item in edition_list})
        edition_date = edition.publish_date.strftime("%d %B %Y")
        current_date_iso = edition.publish_date.isoformat()
        current_city = edition.city
        current_section = edition.section
        current_page = 1
        seo_title = f"{edition.city} {edition.section} E-Paper - {edition_date}"
        seo_description = (
            f"Read Gargachary Times {edition.city} {edition.section} "
            f"e-paper for {edition_date}."
        )
    else:
        editions = ["Metro edition"]
        sections = ["Main"]
        pages = []
        edition_date = "No edition selected"
        current_date_iso = ""
        current_city = ""
        current_section = ""
        current_page = 1
        seo_title = "E-Paper Reader | Gargachary Times"
        seo_description = "Read Gargachary Times e-paper online."

    initial_page = pages[current_page - 1] if pages else None
    initial_page_record = page_records[current_page - 1] if edition and page_records else None
    canonical_url = public_absolute_url(request, request.path)
    share_image_url = get_share_image_url(initial_page_record)
    fallback_image_url = static("site_logo.jpg")
    absolute_image_url = public_absolute_url(request, share_image_url or fallback_image_url)
    share_version = edition.created_at.strftime("%Y%m%d%H%M%S") if edition else "latest"
    whatsapp_share_url = f"{canonical_url}?share={share_version}"

    context = {
        "edition": edition,
        "edition_list": edition_list,
        "editions": editions,
        "sections": sections,
        "pages": pages,
        "current_page": current_page,
        "initial_page": initial_page,
        "edition_date": edition_date,
        "current_date_iso": current_date_iso,
        "current_city": current_city,
        "current_section": current_section,
        "editions_meta": editions_meta,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "canonical_url": canonical_url,
        "whatsapp_share_url": whatsapp_share_url,
        "absolute_image_url": absolute_image_url,
    }
    return render(request, "reader/index.html", context)


def upload_edition(request):
    if request.method == "POST":
        form = EditionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            edition = form.save()
            convert_pdf_to_pages(edition)
            messages.success(request, "PDF uploaded and converted into e-paper pages.")
            return redirect(reverse("reader:edition", kwargs={"pk": edition.pk}))
    else:
        form = EditionUploadForm()

    return render(request, "reader/upload.html", {"form": form})
