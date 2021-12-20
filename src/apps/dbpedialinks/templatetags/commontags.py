from django import template
from django.urls import reverse
import re
import rdflib

# from config.linkeddata.triplestore import *

register = template.Library()


@register.filter()
def powerup(x):
    """
    Make sizes more interesting for force directed graph 
    """
    try:
        xmax = 500
        xmin = 1
        out = (x - xmin) / (xmax - xmin) * 100
        print(x, "becomes", out)
        return out
    except:
        return s


@register.filter(name='trim_unwanted_words')
def trim_unwanted_words(s):
    """
    Remove 'abstract' keyword from text
    """
    try:
        if s.startswith("Abstract"):
            return s[8:]
    except:
        return s


@register.filter(name='tagcloud_sizing')
def tagcloud_sizing(n, base=7):
    """
    For the tag cloud on several pages
    """
    BASE = base
    MAX = 30
    try:
        if n <= BASE:
            return BASE
        else:
            t = BASE + ((BASE * (n - 1)) / 7)
            if t > MAX:
                return MAX
            else:
                return t
    except:
        return BASE


@register.filter(name='tagcloud_opacity')
def tagcloud_opacity(n):
    """
    For the tag cloud on some pages - between 0 and 1
    """
    if n:
        if n <= 9:
            return n / 10.0 + 0.3  # otherwise you don't see it
        elif n >= 10:
            return 1
    else:
        print(
            "ERROR: tags tot count needs to be a number (did you run python manage.py tags_totcount ?"
        )


@register.filter
def url_last_bit(uri):
    """
    Gets the last path element of a url
    """
    try:
        return url.split("/")[-1]
    except:
        return ""


@register.filter
def is_link(stringa):
    """
    Try to determine if a URL is internal to the LOD browser
    """
    if stringa:
        if type(stringa) == rdflib.term.URIRef:
            stringa = unicode(stringa)

        if not stringa.startswith("http://"):
            return False

        return True
    return False


@register.filter
def qname(uri, d3plus=False):
    """
    Try to determine a qname for a URI
    new version 2017-02-13
    """
    if type(uri) != rdflib.term.URIRef:
        # transform into rdflib URIRef so to use namespace_manager on it
        if uri and uri.startswith("http://"):
            uri = rdflib.term.URIRef(uri)
    # now main routine:
    if uri and type(uri) == rdflib.term.URIRef:
        try:
            graph = rdflib.Graph()
            for k, v in NAMESPACES.items():
                graph.bind(k, rdflib.Namespace(v))
            # uri = graph.namespace_manager.compute_qname(uri, generate=False)
            uri = graph.namespace_manager.normalizeUri(uri)
        except:
            pass
    if d3plus:
        uri = uri.replace("<", "").replace(">", "")
    return uri


@register.filter
def qname_custom(uri, d3plus=False):
    """
    Try to determine a qname for a URI
    My own implementation..
    d3plus: removes hashes so to make sure it renders in d3 viz
    """
    if type(uri) != rdflib.term.URIRef:
        # transform into rdflib URIRef so to use namespace_manager on it
        if uri and uri.startswith("http://"):
            uri = rdflib.term.URIRef(uri)
    NS = [(k, rdflib.URIRef(v)) for k, v in NAMESPACES.items()]
    # print NS
    result = uri2niceString(uri, NS)
    if d3plus:
        result = result.replace("<", "").replace(">", "")
        # .replace("\"", "").replace("'", "")
        return result
    else:
        return result


@register.filter
def make_d3plus_id(stringa):
    """
    2016-10-11: hack to see what works
    """
    rx = re.compile('\W+')
    res = rx.sub('-', stringa).strip()
    return res[:20]


@register.filter
def url_last_bit(uri):
    """
    Returns last bit of a url (=path or params)
    (Used to simulate class name from URI in seach)
    """
    try:
        uri = uri.rsplit('/', 1)[1]
        if uri == "2008":
            uri = "for-codes"
    except:
        pass
    return uri


@register.filter
def el_in_keys(ddict, el):
    """
    Checks if a dict has element in its keys
    """
    if el in ddict.keys():
        return True
    else:
        return False


@register.filter
def hashsafe(uri):
    """
    Replaces a hash in a URI with a symbol, so to allow passing it in GET requests
    """
    if type(uri) == rdflib.term.URIRef:
        return unicode(uri).replace("#", HASH_SYMBOL)
    else:
        if uri.startswith("http://"):
            return uri.replace("#", HASH_SYMBOL)


@register.filter
def is_good_link(uri):
    """
    check if a URI should be transformed into a dereferensable link (taking into account LINKEDDATA_HOST setting)
    """
    if uri:
        if type(uri) == rdflib.term.URIRef:
            uri = unicode(uri)

        if not uri.startswith("http://"):
            return False

        if LINKEDDATA_HOST and LINKEDDATA_HOST not in uri:
            return False

        return True
    return False


def uri2niceString(aUri, namespaces=None):
    """
    From a URI, returns a nice string representation that uses also the namespace symbols
    Cuts the uri of the namespace, and replaces it with its shortcut (for base, attempts to infer it or leaves it blank)

    Namespaces are a list

    [('xml', rdflib.URIRef('http://www.w3.org/XML/1998/namespace'))
    ('', rdflib.URIRef('http://cohereweb.net/ontology/cohere.owl#'))
    (u'owl', rdflib.URIRef('http://www.w3.org/2002/07/owl#'))
    ('rdfs', rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#'))
    ('rdf', rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
    (u'xsd', rdflib.URIRef('http://www.w3.org/2001/XMLSchema#'))]

    """
    if not namespaces:
        namespaces = NAMESPACES_DEFAULT

    if type(aUri) == rdflib.term.URIRef:
        # we have a URI: try to create a qName
        stringa = aUri.toPython()
        for aNamespaceTuple in namespaces:
            try:  # check if it matches the available NS
                if stringa.find(aNamespaceTuple[1].__str__()) == 0:
                    if aNamespaceTuple[0]:  # for base NS, it's empty
                        stringa = aNamespaceTuple[0] + ":" + stringa[len(
                            aNamespaceTuple[1].__str__()):]
                    else:
                        prefix = inferNamespacePrefix(aNamespaceTuple[1])
                        if prefix:
                            stringa = prefix + ":" + stringa[len(
                                aNamespaceTuple[1].__str__()):]
                        else:
                            stringa = ":" + stringa[len(aNamespaceTuple[1].
                                                        __str__()):]
            except:
                stringa = "error"

    elif type(aUri) == rdflib.term.Literal:
        stringa = "\"%s\"" % aUri  # no string casting so to prevent encoding errors
    else:
        # print(type(aUri))
        if type(aUri) == type(u''):
            stringa = aUri
        else:
            stringa = aUri.toPython()
    return stringa


def inferNamespacePrefix(aUri):
    """
    From a URI returns the last bit and simulates a namespace prefix when rendering the ontology.

    eg from <'http://www.w3.org/2008/05/skos#'>
        it returns the 'skos' string
    """
    stringa = aUri.__str__()
    try:
        prefix = stringa.replace("#", "").split("/")[-1]
    except:
        prefix = ""
    return prefix
