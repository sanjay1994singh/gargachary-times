from django.shortcuts import render
from .models import NewsPDF


def news_pdf(request):
    selected_date = request.GET.get("date")

    qs = NewsPDF.objects.all()
    if selected_date:
        qs = qs.filter(uploaded_at__date=selected_date)

    current_pdf = qs.last()

    absolute_image_url = (
        request.build_absolute_uri(current_pdf.featured_image.url)
        if current_pdf and current_pdf.featured_image
        else ""
    )

    context = {
        'pdf': current_pdf,
        'news': current_pdf,
        'absolute_image_url': absolute_image_url,
    }

    return render(request, 'news_pdf.html', context)


def new_news_pdf(request):
    news = NewsPDF.objects.order_by('-uploaded_at').first()
    try:
        absolute_image_url = request.build_absolute_uri(news.featured_image.url)
    except:
        absolute_image_url = ''

    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
    }
    return render(request, 'share_pdf.html', context)
