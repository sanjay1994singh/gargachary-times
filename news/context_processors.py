from category.models import Category, State
from django.db.models import Prefetch


def category_context(request):
    states = State.objects.prefetch_related(
        Prefetch(
            'category_set',
            queryset=Category.objects.filter(city=True).order_by('name')
        )
    ).order_by('name')

    other_categories = Category.objects.filter(city=False).order_by('name')

    return {
        'states': states,
        'other_categories': other_categories,
    }
