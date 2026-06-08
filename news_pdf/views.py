from django.shortcuts import render
from .models import NewsPDF
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import NewsPDFSerializer

from datetime import datetime


@api_view(['GET'])
def epaper_list(request):
    date_str = request.GET.get('date')  # 27/01/2026

    if date_str:
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
            epaper = NewsPDF.objects.filter(
                uploaded_at__date=date_obj
            ).order_by('-uploaded_at').first()
        except ValueError:
            return Response({
                "error": "Invalid date format. Use DD/MM/YYYY"
            }, status=400)
    else:
        epaper = NewsPDF.objects.order_by('-uploaded_at').first()

    if epaper:
        serializer = NewsPDFSerializer(
            epaper,
            context={'request': request}
        )
        return Response({"epaper": serializer.data})

    return Response({
        "epaper": None,
        "message": "No epaper found"
    })


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

    return render(request, 'news_pdf1.html', context)


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
