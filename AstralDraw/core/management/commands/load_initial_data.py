from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = "Load initial database JSON data"

    def handle(self, *args, **kwargs):
        # Path to your JSON data file
        json_file = os.path.join(os.path.dirname(__file__), '../../../initial_data.json')
        if os.path.exists(json_file):
            self.stdout.write(self.style.SUCCESS(f"Loading data from {json_file}..."))
            call_command('loaddata', json_file)
            self.stdout.write(self.style.SUCCESS("Data loaded successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"JSON file {json_file} not found!"))
