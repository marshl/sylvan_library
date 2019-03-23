"""
Module for the update_database command
"""
import logging
import time
from django.core.management.base import BaseCommand

logger = logging.getLogger('django')

# pylint: disable=abstract-method
class DataImportCommand(BaseCommand):
    """
    The command for updating hte database
    """

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.update_counts = dict()
        self.created_counts = dict()
        self.ignored_counts = dict()
        self.start_time = time.time()

        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def increment_updated(self, object_type: str):
        """
        Increments the number of objects that were updated
        :param object_type: The type of object that was updated
        :param object_type:
        """
        if object_type not in self.update_counts:
            self.update_counts[object_type] = 0

        self.update_counts[object_type] += 1

    def increment_created(self, object_type: str):
        """
        Increments the number of objects that were created
        :param object_type: The type of object that was created
        """
        if object_type not in self.created_counts:
            self.created_counts[object_type] = 0

        self.created_counts[object_type] += 1

    def increment_ignores(self, object_type: str):
        """
        Increments the number of objects that were ignored
        :param object_type: The type of object that was ignored
        """
        if object_type not in self.ignored_counts:
            self.ignored_counts[object_type] = 0

        self.ignored_counts[object_type] += 1

    def log_stats(self):
        """
        Logs all updated/created/ignored objects
        """
        logger.info('%s', '\n' + ('=' * 80) + '\n\nUpdate complete:\n')
        elapsed_time = time.time() - self.start_time
        logger.info('Time elapsed: %s', time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
        for key, value in self.created_counts.items():
            logger.info('Created %s %s', key, value)

        for key, value in self.update_counts.items():
            logger.info('Updated %s %s', key, value)

        for key, value in self.ignored_counts.items():
            logger.info('Ignored %s %s', key, value)
