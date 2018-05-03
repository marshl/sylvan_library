from django.core.management.base import BaseCommand
from sylvan_library.database_connections import DATABASES as database_list
import os
import subprocess
import datetime
import re


class Command(BaseCommand):
    help = 'Backs up the database'

    def handle(self, *args, **options):
        for key, database in database_list.items():
            os.environ['PGPASSWORD'] = database['PASSWORD']
            now = datetime.datetime.now()
            filename = database['NAME'] + '_' + re.sub('\D', '_', now.isoformat())
            output_file = os.path.join('data_import', 'backup', filename)
            cmd = 'pg_dump -U ' + database['USER'] + ' -d ' + \
                  database['NAME'] + '| 7z a ' + output_file + '.7z -si' + filename + '.sql'
            ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ps.wait()
