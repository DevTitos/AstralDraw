# arena/management/commands/quick_populate.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Quickly populate the arena with essential sample data'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Quick-populating Astral Arena...')
        
        # Run the main populate command
        #call_command('populate_arena')
        
        # Create some active games
        call_command('create_active_games')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Astral Arena ready for demonstration!')
        )