import json
import os
from django.core.management.base import BaseCommand
from fixings.models import Index, Currency


class Command(BaseCommand):
    help = "Добавляет акции в БД из файла indexes.json"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), "indexes.json")

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Файл {file_path} не найден!"))
            return

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        indexes = data.get("indexes", [])
        created_count = 0

        for index in indexes:
            ccyId = Currency.objects.filter(currency=index["ccyId"]).first()
            stock, created = Index.objects.get_or_create(
                indexName=index["indexName"],
                ccyId=ccyId,
                indexISIN=index["indexISIN"]
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Добавлено {created_count} новых акций."))
