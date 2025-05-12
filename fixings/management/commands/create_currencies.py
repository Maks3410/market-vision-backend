import json
import os
from django.core.management.base import BaseCommand
from fixings.models import Currency


class Command(BaseCommand):
    help = "Добавляет валюты в БД из файла currencies.json"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), "currencies.json")

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Файл {file_path} не найден!"))
            return

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        currencies = data.get("currencies", [])
        created_count = 0

        for currency_data in currencies:
            currency, created = Currency.objects.get_or_create(
                currency=currency_data["currency"],
                symbol=currency_data["symbol"],
                ticker=f"{currency_data['currency']}USD=X"
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Добавлено {created_count} новых валют."))
