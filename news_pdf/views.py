from django.shortcuts import render
from .models import NewsPDF
from datetime import date

# Create your views here.
def news_pdf(request):
    selected_date = request.GET.get("date")

    if selected_date:
        # filter by date part of uploaded_at
        latest_pdf = NewsPDF.objects.filter(
            uploaded_at__date=selected_date
        ).first()
        absolute_image_url = request.build_absolute_uri(latest_pdf.featured_image.url)
    else:
        # fallback → latest PDF
        latest_pdf = NewsPDF.objects.last()
        absolute_image_url = request.build_absolute_uri(latest_pdf.featured_image.url)
    context = {
        'pdf': latest_pdf,
        'absolute_image_url': absolute_image_url,
    }
    return render(request, 'news_pdf.html', context)


def news_pdf1(request):
    selected_date = request.GET.get("date")

    if selected_date:
        # filter by date part of uploaded_at
        latest_pdf = NewsPDF.objects.filter(
            uploaded_at__date=selected_date
        ).first()
        absolute_image_url = request.build_absolute_uri(latest_pdf.featured_image.url)
    else:
        # fallback → latest PDF
        latest_pdf = NewsPDF.objects.last()
        absolute_image_url = request.build_absolute_uri(latest_pdf.featured_image.url)

    context = {
        'pdf': latest_pdf,
        'absolute_image_url': absolute_image_url,
    }
    print(context, '=============context')
    return render(request, 'news_pdf1.html', context)
