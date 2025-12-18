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
    else:
        latest_pdf = NewsPDF.objects.last()
        current_pdf = NewsPDF.objects.get(id=latest_pdf.id)

    absolute_image_url = request.build_absolute_uri(current_pdf.featured_image.url)

    context = {
        'news': current_pdf,
        'absolute_image_url': absolute_image_url,
    }

    return render(request, 'pdf.html', context)
    return render(request, 'news_pdf.html', context)
