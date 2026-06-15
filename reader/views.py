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
    else:
        editions = ["Metro edition"]
        sections = ["Main"]
        pages = []
        edition_date = "No edition selected"
        current_date_iso = ""
        current_city = ""
        current_section = ""
        current_page = 1

    initial_page = pages[current_page - 1] if pages else None

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
