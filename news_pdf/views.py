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
    else:
        # fallback → latest PDF
        latest_pdf = NewsPDF.objects.last()
    return render(request, 'news_pdf.html', {'pdf': latest_pdf})
