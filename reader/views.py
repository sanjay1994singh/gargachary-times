from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import EditionUploadForm
from .models import Edition
from .services import convert_pdf_to_pages


def reader_home(request, pk=None):
    edition = get_object_or_404(Edition, pk=pk) if pk else Edition.objects.first()
    edition_list = Edition.objects.all()
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
    canonical_url = request.build_absolute_uri()
    absolute_image_url = (
        request.build_absolute_uri(initial_page["image"])
        if initial_page else ""
    )

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
