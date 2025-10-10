from django.db import models


class NewsPDF(models.Model):
    title = models.CharField(max_length=200)
    featured_image = models.ImageField(upload_to='news_image', null=True)
    pdf_file = models.FileField(upload_to='news_pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'news_pdf'
