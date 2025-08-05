from django.shortcuts import render
from .models import NewsPDF


# Create your views here.
def news_pdf(request):
    latest_pdf = NewsPDF.objects.last()
    return render(request, 'news_pdf.html', {'pdf': latest_pdf})
