# HOW TO

# https://docs.djangoproject.com/en/1.10/howto/custom-management-commands/

# [a]: attempt one doc at a time
# 1. read Doc from DB
# 2. get record in elastic (external drive) using URI
# 3. extract Title, DOI, pubyear, journal if available
# 4. write back to DB

# fast enough? otherwise i can try getmany API

# python manage.py cmd_enrich_from_elastic

import sys
import json
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import DataError

from dbpedialinks.models import *
from myutils.myutils import *
from elasticsearch import Elasticsearch


def pretty_json(dict):
    return json.dumps(dict, indent=4, sort_keys=True)


def writerr(x):
    sys.stderr.write(x)


HOST = "http://127.0.0.1:9200/"
INDEX = "full_text_search_live"
es = Elasticsearch(hosts=HOST)


class Command(BaseCommand):
    help = 'Load dbpedia links data from file'

    # def add_arguments(self, parser):
    #     parser.add_argument('filename', nargs='?', default=False, help="specify which TTL file to parse")

    def handle(self, *args, **options):

        # if not options['filename']:
        #     print "Please provide an argument: <filename.ttl>"
        #     return

        counter = 0
        for doc in SGDocument.objects.filter(title=None):
            if doc.uri:
                counter += 1
                print(counter, doc.uri)
                res = es.get(index=INDEX, doc_type="_all", id=doc.uri)
                jsonld = res['_source']['rdf']

                try:
                    doi = jsonld[
                        'http://scigraph.springernature.com/ontologies/core/doi'][
                            0]['@value']
                except:
                    doi = None
                    print("==== ERROR getting DOI / skipping")

                try:
                    year = jsonld[
                        'http://scigraph.springernature.com/ontologies/core/publicationYear'][
                            0]["@value"]
                except:
                    year = None
                    print("==== ERROR getting pubYear - continuing")

                try:
                    title = jsonld[
                        "http://scigraph.springernature.com/ontologies/core/title"][
                            0]["@value"]
                except:
                    title = None
                    print("==== ERROR getting title / skipping")
                    continue

                try:
                    year = int(year)
                except:
                    year = None

                print("*", doi, year, title)

                if False:
                    return  # testing

                if True:
                    if doi or year or title:
                        doc.title = title
                        doc.pubyear = year
                        doc.description = doi
                        doc.save()

        print("Done - objects created!")
