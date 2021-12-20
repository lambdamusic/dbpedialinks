#!/usr/bin/python
# -*- coding: utf-8 -*-


import rdflib



def qname(uri, namespaces_dict, strip_html_tags=False):
    """
    Try to determine a qname for a URI

    namespaces: dictionary of namespaces
    strip_html_tags: flag to remove < and > as needed by some JS visualizations
    """
    if type(uri) != rdflib.term.URIRef:
        # transform into rdflib URIRef so to use namespace_manager on it
        if uri and uri.startswith("http://"):
            uri = rdflib.term.URIRef(uri)
    # now main routine:
    if uri and type(uri) == rdflib.term.URIRef:
        try:
            graph = rdflib.Graph()
            for k,v in namespaces_dict.items():
                graph.bind(k, rdflib.Namespace(v))
            if False:
                # note: this is the proper way but it fails in some cases!
                # BUG: https://github.com/RDFLib/rdflib/issues/763
                uri = graph.namespace_manager.normalizeUri(uri)
            else:
                # my own implementation
                NS = [(k, rdflib.URIRef(v)) for k,v in namespaces_dict.items()]
                uri = uri2niceString(uri, NS)
        except:
            pass
    if strip_html_tags:
        uri = uri.replace("<", "").replace(">", "")
    return uri







def ttlNamespaces2Dict(ttl_text):
    """
    reads a TTL declaration of namespaces and returns a dict of the form
    {
    "sg": "http://name.scigraph.com/ontologies/core/" ,
    "sgc": "http://name.scigraph.com/core/",
    # etc..
    }
    """
    exit = {}
    for line in ttl_text.split("\n"):
        line = line.strip()
        if line.startswith("@prefix"):
            prefix = line.split()[1].replace(":", "")
            ns = line.split()[2].replace("<", "").replace(">", "")
            exit[prefix] = ns
    return exit






def firstStringInList(literalEntities, prefLanguage="en"):
    """
    from a list of literals, returns the one in prefLanguage
    if no language specification is available, return first element
    """
    match = ""

    if len(literalEntities) == 1:
        match = literalEntities[0]
    elif len(literalEntities) > 1:
        for x in literalEntities:
            if getattr(x, 'language') and  getattr(x, 'language') == prefLanguage:
                match = x
        if not match: # don't bother about language
            match = literalEntities[0]
    return match






def uri2niceString(aUri, namespaces = None):
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
            try: # check if it matches the available NS
                if stringa.find(aNamespaceTuple[1].__str__()) == 0:
                    if aNamespaceTuple[0]: # for base NS, it's empty
                        stringa = aNamespaceTuple[0] + ":" + stringa[len(aNamespaceTuple[1].__str__()):]
                    else:
                        prefix = inferNamespacePrefix(aNamespaceTuple[1])
                        if prefix:
                            stringa = prefix + ":" + stringa[len(aNamespaceTuple[1].__str__()):]
                        else:
                            stringa = ":" + stringa[len(aNamespaceTuple[1].__str__()):]
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
