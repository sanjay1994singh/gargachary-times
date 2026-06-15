from django.contrib import admin

from .models import Edition, EditionPage
from .services import convert_pdf_to_pages


class EditionPageInline(admin.TabularInline):
    model = EditionPage
    extra = 0
    readonly_fields = ["number", "image"]


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ["city", "section", "publish_date", "created_at"]
    search_fields = ["city", "section"]
    readonly_fields = ["created_at"]
    inlines = [EditionPageInline]

    def save_model(self, request, obj, form, change):
        pdf_changed = not change or "pdf" in form.changed_data
        super().save_model(request, obj, form, change)

        if pdf_changed:
            page_count = convert_pdf_to_pages(obj)
            self.message_user(
                request,
                f"PDF converted successfully. {page_count} page(s) created.",
            )


@admin.register(EditionPage)
class EditionPageAdmin(admin.ModelAdmin):
    list_display = ["edition", "number"]
