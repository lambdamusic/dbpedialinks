# HOW TO

# https://docs.djangoproject.com/en/1.10/howto/custom-management-commands/

# python manage.py cmd_subjects_optimize

import sys
from django.core.management.base import BaseCommand

from dbpedialinks.models import *
from myutils.myutils import *


class Command(BaseCommand):
    help = 'command to calc tot counts for tags / so to make tagcloud faster'

    def handle(self, *args, **options):

        # change True/False as needed..

        if False:
            # 1: cache the total count

            tot = DBPediaEntity.objects.count()
            counter = 0
            for x in DBPediaEntity.objects.all():
                counter += 1
                x.update_tot_count()
                print("{}/{} - {}".format(counter, tot, x.title))

            print("Done - objects created!")

        if True:
            tot = DBPediaEntity.objects.count()
            counter = 0
            for x in DBPediaEntity.objects.all():
                counter += 1
                print("{}/{} - {}".format(counter, tot, x.title))
                x.related_subjects(size=10, CACHE=True)

            print("Done - objects created!")
