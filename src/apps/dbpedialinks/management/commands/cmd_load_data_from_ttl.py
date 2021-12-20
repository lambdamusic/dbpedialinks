# HOW TO

# https://docs.djangoproject.com/en/1.10/howto/custom-management-commands/

# cd /Users/michele.pasin/dev/knowledge-graph/scigraph-experiments/src
# workon sg-prototypes
# python manage.py cmd_load_data_from_ttl

import sys
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import DataError

from dbpedialinks.models import *
from myutils.myutils import *


def writerr(x):
    sys.stderr.write(x)


BASEDIR = "/Users/michele.pasin/Downloads/sci-graph-links-master/named-entity-recognition/produced-data/book-chapters/085confidence/dbpedia-backlinks/"
FILES = [('dbpedia-bl1-085.ttl', 0), ('dbpedia-bl2-085.ttl', 0),
         ('dbpedia-bl3-085.ttl', 0), ('dbpedia-bl4-085.ttl', 0),
         ('dbpedia-bl5-085.ttl', 0), ('dbpedia-bl6-085.ttl', 0),
         ('dbpedia-bl7-085.ttl', 0), ('dbpedia-bl-085.ttl', 0)]


class Command(BaseCommand):
    help = 'Load dbpedia links data from file'

    # def add_arguments(self, parser):
    #     parser.add_argument('filename', nargs='?', default=False, help="specify which TTL file to parse")

    def handle(self, *args, **options):

        if False:
            # manual switch for erasing the DB
            print("DELETING!")
            SGDocument.objects.all().delete()
            DBPediaEntity.objects.all().delete()
            return

        # if not options['filename']:
        #     print "Please provide an argument: <filename.ttl>"
        #     return

        counter_f = 0
        for filename_group in FILES:
            counter_f += 1
            filename = filename_group[0]
            start_from = filename_group[1]

            with open(BASEDIR + filename) as f:

                counter = 0

                for line in f:
                    counter += 1
                    if start_from <= counter:
                        uris = get_uris(line)

                        doc_uri = remove_offset(uris[0])
                        entity_uri = uris[2]
                        entity_title = infer_title(uris[2])
                        c1, c2 = False, False

                        doc, c1 = SGDocument.objects.get_or_create(uri=doc_uri)

                        entity, c2 = DBPediaEntity.objects.get_or_create(
                            uri=entity_uri, title=entity_title)
                        # print entity_uri
                        try:
                            print(
                                "[%s/%d] %s [created=%r] => %s [created=%r]" %
                                (filename, counter, doc, c1, entity.title, c2))
                        except:
                            print("[%s/%d] %s [created=%r] => URI [created=%r]"
                                  % (filename, counter, doc, c1, c2))

                        doc.dbentities.add(entity)
                    else:
                        print("Skipping line %d" % counter)

        print("Done - objects created!")


def get_uris(line):
    "from an RDF N3 line, extract the URIs in it"
    items = line.split(" ")
    items = [x.replace("<", "").replace(">", "") for x in items]
    return items


def remove_offset(uri_string):
    """From a SciGraph URI with offset (http://scigraph.springernature.com/things/articles/4545218dc0eb528cdc3a9f869758a907#offset_496_503) remove the offset infos"""
    return uri_string.split("#")[0]


def infer_title(uri_string):
    """From a DBpedia resource URI (http://dbpedia.org/resource/Color_difference) only return the last bit"""
    return uri_string.replace("http://dbpedia.org/resource/", "").replace(
        "_", " ")
