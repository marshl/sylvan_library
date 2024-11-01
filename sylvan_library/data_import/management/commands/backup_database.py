"""
The module for the backup_database command
"""

import os
import subprocess
import datetime
import logging
import re
from typing import Any

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for backing up the database
    """

    help = "Backs up the database"

    def handle(self, *args: Any, **options: Any) -> None:
        for key, database in settings.DATABASES.items():
            logger.info("Backing up database %s", key)
            os.environ["PGPASSWORD"] = database["PASSWORD"]
            now = datetime.datetime.now()
            filename = database["NAME"] + "_" + re.sub(r"\D", "_", now.isoformat())
            output_file = os.path.join("data_import", "backup", filename)
            cmd = (
                "pg_dump -U "
                + database["USER"]
                + " -d "
                + database["NAME"]
                + " --host "
                + database["HOST"]
                + " --port "
                + str(database["PORT"])
                + "| 7z a "
                + output_file
                + ".7z -si"
                + filename
                + ".sql"
            )
            logger.info(cmd)
            process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            process.wait()
