# management/commands/setup_governance.py
from django.core.management.base import BaseCommand
from governance.models import GovernanceTopic

class Command(BaseCommand):
    help = 'Setup initial governance topics'
    
    def handle(self, *args, **options):
        topics = [
            {
                'topic_id': '0.0.7174429',
                'name': 'The Launchpad',
                'description': 'Project proposals and investments'
            },
            {
                'topic_id': '0.0.7174434',
                'name': 'The Cosmic Clock', 
                'description': 'Lottery frequency and parameters'
            },
            {
                'topic_id': '0.0.7174439',
                'name': 'The Nebula Split',
                'description': 'Prize distribution formulas'
            },
            {
                'topic_id': '0.0.7174440', 
                'name': 'The Galactic Forum',
                'description': 'General community discussions'
            }
        ]
        
        for topic_data in topics:
            topic, created = GovernanceTopic.objects.get_or_create(
                topic_id=topic_data['topic_id'],
                defaults=topic_data
            )
            if created:
                self.stdout.write(f"Created topic: {topic.name}")
        
        self.stdout.write(self.style.SUCCESS('Successfully setup governance topics'))