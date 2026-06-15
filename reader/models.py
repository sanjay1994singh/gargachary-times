from django.db import models


class Edition(models.Model):
    city = models.CharField(max_length=120)
    section = models.CharField(max_length=80, default="Main")
    publish_date = models.DateField()
    pdf = models.FileField(upload_to="editions/pdfs/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-publish_date", "-created_at"]

    def __str__(self):
        return f"{self.city} - {self.section} - {self.publish_date:%d %b %Y}"


class EditionPage(models.Model):
    edition = models.ForeignKey(Edition, related_name="pages", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    image = models.FileField(upload_to="editions/pages/")

    class Meta:
        ordering = ["number"]
        unique_together = ("edition", "number")

    def __str__(self):
        return f"{self.edition} page {self.number:02d}"
