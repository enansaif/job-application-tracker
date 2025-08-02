import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        connection = None
        max_attempt = 10
        while max_attempt > 0:
            try:
                connection = connections['default']
                connection.cursor()  # make connection attempt
                self.stdout.write('Database initialized.')
                return
            except OperationalError:
                self.stdout.write('Waiting for database to initialize...')
                max_attempt -= 1
                time.sleep(1)
        self.stdout.write('Could not initialize database')
