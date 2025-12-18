from django.shortcuts import render
from .models import NewsPDF


# Create your views here.
def news_pdf(request):
    selected_date = request.GET.get("date")
    if selected_date:
        latest_pdf = NewsPDF.objects.filter(
            uploaded_at__date=selected_date
        ).first()
        current_pdf = NewsPDF.objects.get(id=latest_pdf.id)

        absolute_image_url = request.build_absolute_uri(current_pdf.featured_image.url)
    else:
        latest_pdf = NewsPDF.objects.last()
        current_pdf = NewsPDF.objects.get(id=latest_pdf.id)
        absolute_image_url = request.build_absolute_uri(current_pdf.featured_image.url)

    context = {
        'pdf': latest_pdf,
        'news': current_pdf,
        'absolute_image_url': absolute_image_url,
    }

    return render(request, 'news_pdf.html', context)

#
# def news_pdf(request):
#     news = NewsPDF.objects.get(id=130)
#     absolute_image_url = request.build_absolute_uri(news.featured_image.url)
#     context = {
#         'news': news,
#         'absolute_image_url': absolute_image_url,
#     }
#
#     return render(request, 'pdf.html', context)
