from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Load initial database data from JSON fixture automatically."

    def handle(self, *args, **kwargs):
        # Look for initial_data.json in the project root
        json_file = os.path.join(settings.BASE_DIR, "initial_data.json")

        if os.path.exists(json_file):
            self.stdout.write(self.style.SUCCESS(f"Loading fixture: {json_file}"))
            try:
                call_command('loaddata', json_file)
                self.stdout.write(self.style.SUCCESS("✅ Initial data loaded successfully!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to load data: {e}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Fixture file not found at {json_file}"))
