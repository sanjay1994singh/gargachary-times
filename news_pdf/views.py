from django.shortcuts import render
from .models import NewsPDF


# Create your views here.
def news_pdf(request):
    selected_date = request.GET.get("date")
    print(selected_date, '=================q')
    if selected_date:
        latest_pdf = NewsPDF.objects.filter(
            uploaded_at__date=selected_date
        ).first()
        current_pdf = NewsPDF.objects.get(id=latest_pdf.id)

        absolute_image_url = request.build_absolute_uri(pdf.featured_image.url)
    else:
        latest_pdf = NewsPDF.objects.last()
        current_pdf = NewsPDF.objects.get(id=latest_pdf.id)
        absolute_image_url = request.build_absolute_uri(pdf.featured_image.url)

    context = {
        'pdf': latest_pdf,
        'news': current_pdf,
        'absolute_image_url': absolute_image_url,
    }

    return render(request, 'news_pdf.html', context)
