# news/context_processors.py

from category.models import Category

def category_context(request):
    return {
        'category': Category.objects.all().order_by('-id')
    }
