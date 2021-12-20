#!/usr/bin/env python
# encoding: utf-8

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlquote
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Q

import string
from time import strftime
from collections import Counter, OrderedDict

import pyscigraph
import ontospy

from render_block import render_block_to_string
from .models import *


class OrderedCounter(Counter, OrderedDict):
    pass


def home(request):
    """
    landing page

    TIPS:

    In [14]: import string

    In [15]: string.letters
    Out[15]: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    In [16]: string.ascii_letters
    Out[16]: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    In [17]: string.ascii_lowercase
    Out[17]: 'abcdefghijklmnopqrstuvwxyz'

    In [18]: string.punctuation
    Out[18]: '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    In [19]: string.printable
    Out[19]: '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'

    """

    letter = request.GET.get("letter", None)
    query = request.GET.get("query", None)

    alphabet = string.ascii_lowercase
    alphabet = alphabet + "*"

    punctuation_and_numbers = string.punctuation + "1234567890"

    entities = []

    if letter:
        if letter == "*":
            filterList = list(punctuation_and_numbers)
            query = Q()
            for x in filterList:
                query = query | Q(title__istartswith=x)
                entities = DBPediaEntity.objects.filter(query)
            query = None  # zero it not to interfere with template logic
        else:
            entities = DBPediaEntity.objects.filter(title__istartswith=letter)

    elif query:
        entities = DBPediaEntity.objects.filter(title__icontains=query)

    context = {
        'articlestot': SGDocument.objects.count(),
        'entitiestot': DBPediaEntity.objects.count(),
        'entities': entities,
        'alphabet': alphabet,
        'thisletter': letter,
        'query': query,
    }

    return render(request, 'dbpedialinks/home.html', context)


def entities(request, entity_id=None):
    """
    landing page + detail for entities
    """

    filters_id = request.GET.getlist("filters")
    context = {}

    entity = get_object_or_404(DBPediaEntity, pk=int(entity_id))

    subject = get_object_or_404(DBPediaEntity, pk=int(entity_id))
    filters = [subject]

    if filters_id:
        filters += [DBPediaEntity.objects.get(pk=int(x)) for x in filters_id]
        print("===== Filters: ", str(filters))
        articles = SGDocument.objects.filter()
        for el in filters:
            articles = articles.filter(dbentities=el)

    else:
        articles = subject.sgdocument_set.all()

        #  create data for dataviz
        SIZE0, SIZE1, SIZE2 = 70, 50, 5
        green, lightgreen, yellow, lightorange, orange, red = 0, 0.4, 0.5, 0.6, 0.7, 0.8
        LVL0, LVL1, LVL2 = yellow, green, lightgreen  # templates uses this to determine color
        # LVL0, LVL1, LVL2 = orange, red, lightorange

        rels = entity.is_subject_in_relations.all(
        )  # NOTE requires cached objects! 2018-11-29
        LINKS = [(x.subject1, x.subject2) for x in rels]
        SEED = [(entity, SIZE0, LVL0)]
        NODES = [(x.subject2, SIZE1, LVL1)
                 for x in rels]  # change with x.score
        NODES_AND_SEED = NODES + SEED  # add home entity by default, PS score drives color
        for node in NODES:
            for x in node[0].is_subject_in_relations.all()[:5]:
                if x.subject2.id not in [n[0].id for n in NODES_AND_SEED]:
                    NODES_AND_SEED += [(x.subject2, SIZE2, LVL2)]
                LINKS += [(x.subject1, x.subject2)]

        context.update({'nodes': NODES_AND_SEED, 'links': LINKS})

    # CO-OCCURRING SUBJECTS
    sorted_related = subject.related_subjects(
        articles_set=articles)  # =>list of tuples (subject, count)
    filters_minus_entity = [f for f in filters if f.id != subject.id]

    context.update({
        'entity': subject,
        'filters': filters,
        'filters_minus_entity': filters_minus_entity,
        'articles': articles,
        'related_subjects': sorted_related,
        # 'related_subjects_graph': sorted_related[:20]
    })

    return render(request, 'dbpedialinks/subject.html', context)


def ajax_tags_info(request):
    """
    Get tag info via ajax

    eg http://scigraph.springernature.com/things/articles/0786393400bb0690ffbbc208884e5271
    """

    sg_id = request.GET.get("id", None)
    print("ID DOCUMENT === ", sg_id)

    article = get_object_or_404(SGDocument, uri=sg_id)

    context = {
        'tags': article.dbentities.all(),
    }

    return_str = render_block_to_string(
        'dbpedialinks/snippet_ajax_tag_info.html', 'tag_info', context)

    return HttpResponse(return_str)


def ajax_dbpedia_info(request):
    """
    Get dbpedia description info via ajax

    eg http://dbpedia.org/resource/Panicum_virgatum
    """

    dbpedia_id = request.GET.get("id", None)
    if "/page/" in dbpedia_id:
        dbpedia_id = dbpedia_id.replace("/page/", "resource/")
    print("ID FOR DBPedia === ", dbpedia_id)

    # load ontospy without generating schema info, but pull out URI entity
    o = ontospy.Ontospy(dbpedia_id, build_all=False)
    e = o.build_entity_from_uri(dbpedia_id)
    if e:
        desc = e.bestDescription()
    else:
        desc = "Entity description not found"

    # context = {
    #     'desc' : desc,
    # }

    # return_str = render_block_to_string('dbpedialinks/snippet_ajax_tag_info.html',
    #                                     'tag_info',
    #                                     context)

    return HttpResponse(desc)


# ===========
# UNUSED AND TESTS
# ===========


def graph_test(request, entity_id=None):
    """
    based on http://bl.ocks.org/eyaler/10586116
    """

    filters_id = request.GET.getlist("filters")
    if entity_id:
        entity = get_object_or_404(DBPediaEntity, pk=int(entity_id))
        context = {
            'entity': entity,
            'related_subjects': entity.related_subjects(10),
        }
    else:
        context = {'entity': None}
    return render(request, 'dbpedialinks/test/graph_test.html', context)


def graph_test_two_levels(request, entity_id=None):
    """
    same as above but passing two levels worth of data to display a more interesting graph
    what changes is the data strucure we send back

    nodes = [list of unique nodes with score]
    links = [list of unique links tuple]
    """

    entity = get_object_or_404(DBPediaEntity, pk=int(entity_id))

    SIZE1 = 50  #testing fix sizes: reads well.. but less interesting in the long run
    SIZE2 = 5
    # requires new cached objects! 2018-11-29
    rels = entity.is_subject_in_relations.all()
    LINKS = [(x.subject1, x.subject2) for x in rels]
    SEED = [(entity, SIZE1)]
    NODES = [(x.subject2, x.score) for x in rels]
    NODES_AND_SEED = NODES + SEED  # add home entity by default, score drives color

    for node in NODES:
        for x in node[0].is_subject_in_relations.all()[:5]:
            if x.subject2.id not in [n[0].id for n in NODES_AND_SEED]:
                NODES_AND_SEED += [(x.subject2, x.score)]
            LINKS += [(x.subject1, x.subject2)]

    context = {'entity': entity, 'nodes': NODES_AND_SEED, 'links': LINKS}

    return render(request, 'dbpedialinks/test/graph_test.2.html', context)


def articles(request, article_id=None):
    """
    landing page + detail for articles
    """
    uri = request.GET.get("uri", None)

    if uri:

        # article = get_object_or_404(SGDocument, pk=int(article_id))
        article = get_object_or_404(SGDocument, uri=uri)

        context = {'article': article}

    else:
        context = {'article': None}

    return render(request, 'dbpedialinks/articles.html', context)


def ajax_scigraph(request):
    """
    Use SG API to get metadata

    eg http://scigraph.springernature.com/things/articles/0786393400bb0690ffbbc208884e5271
    """

    sg_id = request.GET.get("id", None)
    print("ID FOR SCIGRAPH === ", sg_id)

    cl = pyscigraph.SciGraphClient()
    e = cl.get_entity_from_id(uri=sg_id)

    if e:
        title = e.title
        doi = e.doi
        abstract = e.getValuesForProperty(
            "http://scigraph.springernature.com/ontologies/core/abstract")
        if abstract: abstract = abstract[0]

        context = {
            'article_id': sg_id,
            'title': title,
            'doi': doi,
            'abstract': abstract,
        }

        return_str = render_block_to_string(
            'dbpedialinks/snippet_ajax_article_info.html', 'article_info',
            context)

        return HttpResponse(return_str)

    else:
        return HttpResponse(
            "Sorry the request timed out - <a href='%s' target='_blank'>try on SciGraph?</a>"
            % sg_id)
