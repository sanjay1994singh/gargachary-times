import re
from datetime import datetime
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import get_valid_filename

from news_pdf.models import NewsPDF
from reader.models import Edition
from reader.services import convert_pdf_to_pages


MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_old_pdf_date(old_pdf):
    text = f"{old_pdf.title or ''} {old_pdf.pdf_file.name or ''}".lower()
    text = text.replace("__", "_")

    numeric_match = re.search(
        r"(?<!\d)(\d{1,2})[ _\-.]+(\d{1,2})[ _\-.]+(\d{4})(?!\d)",
        text,
    )
    if numeric_match:
        day, month, year = map(int, numeric_match.groups())
        try:
            return datetime(year, month, day).date()
        except ValueError:
            pass

    month_match = re.search(
        r"(?<!\d)(\d{1,2})[ _\-.]+([a-z]+)[ _\-.]+(\d{4})(?!\d)",
        text,
    )
    if month_match:
        day = int(month_match.group(1))
        month = MONTHS.get(month_match.group(2))
        year = int(month_match.group(3))
        if month:
            try:
                return datetime(year, month, day).date()
            except ValueError:
                pass

    iso_match = re.search(
        r"(?<!\d)(\d{4})[ _\-.]+(\d{1,2})[ _\-.]+(\d{1,2})(?!\d)",
        text,
    )
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        try:
            return datetime(year, month, day).date()
        except ValueError:
            pass

    return old_pdf.uploaded_at.date()


class Command(BaseCommand):
    help = "Copy old NewsPDF records into the new reader Edition model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what will import without creating editions or converting pages.",
        )
        parser.add_argument(
            "--city",
            default="Mathura",
            help="Default city for imported old PDFs.",
        )
        parser.add_argument(
            "--section",
            default="Main",
            help="Default section for imported old PDFs.",
        )
        parser.add_argument(
            "--zoom",
            type=float,
            default=2,
            help="PDF render zoom for generated reader pages.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        city = options["city"]
        section = options["section"]
        zoom = options["zoom"]

        imported = 0
        skipped = 0
        missing = 0
        failed = 0

        old_pdfs = NewsPDF.objects.order_by("uploaded_at", "id")

        for old_pdf in old_pdfs:
            if not old_pdf.pdf_file:
                missing += 1
                self.stdout.write(
                    self.style.WARNING(f"Missing file field: NewsPDF #{old_pdf.pk}")
                )
                continue

            source_name = old_pdf.pdf_file.name
            original_name = get_valid_filename(Path(source_name).name)
            target_name = f"editions/pdfs/imported/newspdf-{old_pdf.pk}-{original_name}"
            publish_date = parse_old_pdf_date(old_pdf)

            if Edition.objects.filter(pdf=target_name).exists():
                skipped += 1
                self.stdout.write(f"Skip existing: NewsPDF #{old_pdf.pk} -> {target_name}")
                continue

            if Edition.objects.filter(pdf=source_name).exists():
                skipped += 1
                self.stdout.write(f"Skip already linked: NewsPDF #{old_pdf.pk} -> {source_name}")
                continue

            if not default_storage.exists(source_name):
                missing += 1
                self.stdout.write(
                    self.style.WARNING(f"File not found: NewsPDF #{old_pdf.pk} -> {source_name}")
                )
                continue

            if dry_run:
                imported += 1
                self.stdout.write(
                    f"Would import: NewsPDF #{old_pdf.pk} | {publish_date} | "
                    f"{source_name} -> {target_name}"
                )
                continue

            edition = None
            try:
                with transaction.atomic():
                    if not default_storage.exists(target_name):
                        with default_storage.open(source_name, "rb") as source_file:
                            target_name = default_storage.save(
                                target_name,
                                ContentFile(source_file.read()),
                            )

                    edition = Edition.objects.create(
                        city=city,
                        section=section,
                        publish_date=publish_date,
                        pdf=target_name,
                    )

                page_count = convert_pdf_to_pages(edition, zoom=zoom)
                imported += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported NewsPDF #{old_pdf.pk} -> Edition #{edition.pk} "
                        f"({publish_date}, {page_count} pages)"
                    )
                )
            except Exception as exc:
                failed += 1
                if edition:
                    edition.delete()
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed NewsPDF #{old_pdf.pk}: {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. imported={imported}, skipped={skipped}, missing={missing}, failed={failed}, "
                f"dry_run={dry_run}"
            )
        )
