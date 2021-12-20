#!/usr/bin/python
# -*- coding: utf-8 -*-


import rdflib
from itertools import count

from .misc import *




class RDFResource(object):
    """
    Pythonic abstraction for any RDF Resource object.

    Allows to store an RDF 'minigraph' containing all metadata associcated to a resource,
    and to query the minigraph e.g. for descriptions, types, class info etc..
    """

    DEFAULT_NAMESPACES = []

    # http://stackoverflow.com/questions/8628123/counting-instances-of-a-class
    _ids = count(0)

    def __init__(self, uri, minigraph, namespaces={}, format="n3"):
        super(RDFResource, self).__init__()
        self.id = next(self._ids)
        self.uri = rdflib.URIRef(uri)
        self.graph = rdflib.Graph()
        self.graph.parse(data=minigraph, format=format)
        self.namespaces =  namespaces
        self.namespaces_sorted =  sorted([ [k,v] for k, v in namespaces.items() ])
        for k,v in self.namespaces.items():
            self.graph.bind(k, rdflib.Namespace(v))

        self.qname = qname(self.uri, self.namespaces)


    def getValuesForProperty(self, aPropURIRef):
        """
        helper method
        generic way to extract some prop value eg
            In [11]: c.getValuesForProperty(rdflib.RDF.type)
            Out[11]:
            [rdflib.term.URIRef(u'http://www.w3.org/2002/07/owl#Class'),
             rdflib.term.URIRef(u'http://www.w3.org/2000/01/rdf-schema#Class')]
        NOTE: the subject is always implicit

        """
        return list(self.graph.objects(self.uri, aPropURIRef))



    def is_class(self):
        test = self.getValuesForProperty(rdflib.RDF.type)
        if rdflib.OWL.Class in test or rdflib.RDFS.Class in test:
            return True
        else:
            return False

    def is_property(self):
        test = self.getValuesForProperty(rdflib.RDF.type)
        if rdflib.OWL.AnnotationProperty in test or rdflib.OWL.DatatypeProperty in test or rdflib.OWL.ObjectProperty in test or rdflib.RDF.Property in test:
            return True
        else:
            return False


    def all_types(self):
        test = self.getValuesForProperty(rdflib.RDF.type)
        return [str(x) for x in test]



    def bestLabel(self, prefLanguage="en"):
        """
        facility for extrating the best available label for an entity

        ..This checks RFDS.label, SKOS.prefLabel and finally the qname local component
        """

        test = self.getValuesForProperty(rdflib.RDFS.label)
        out = ""

        if test:
            out = firstStringInList(test)
        else:
            test = self.getValuesForProperty(rdflib.namespace.SKOS.prefLabel)
            if test:
                out = firstStringInList(test)
            else:
                test = self.getValuesForProperty(rdflib.URIRef("http://www.springernature.com/scigraph/ontologies/core/title"))
                if test:
                    out = firstStringInList(test)

        if not out:
            out = self.qname # default
        return out



    def bestDescription(self, prefLanguage="en"):
        """
        facility for extrating the best available description for an entity

        ..This checks RFDS.label, SKOS.prefLabel and finally the qname local component
        """

        test_preds = [rdflib.RDFS.comment, rdflib.namespace.DCTERMS.description, rdflib.namespace.DC.description, rdflib.namespace.SKOS.definition ]

        for pred in test_preds:
            test = self.getValuesForProperty(pred)
            if test:
                return firstStringInList(test)
        return ""



    def triples(self, unique_nodes=False, unique_predicates=False, unique_subjobj=False):
        """
        return all triples in the minigraph having the primary instance URI as subject
        (note: there may be other triples in the minigraph but we're not returning them)

        unique_nodes => if True, return a list of the unique nodes for these triples (including literals)
        unique_predicates => returns a list of only the predicates
        unique_subjobj => returns a list of only the subj/obj
        """
        if unique_nodes:
            exit = [self.uri]
            for x, y, z in self.graph.triples((self.uri, None, None)):
                exit += [y, z]  # NOTE: x is already in the exit list (=> self.uri)
            return list(set(exit))
        elif unique_predicates:
            exit = []
            for x, y, z in self.graph.triples((self.uri, None, None)):
                exit += [y]
            return list(set(exit))
        elif unique_subjobj:
            exit = [self.uri]
            for x, y, z in self.graph.triples((self.uri, None, None)):
                exit += [z]  # NOTE: x is already in the exit list (=> self.uri)
            return list(set(exit))
        else:
            return sorted(list(self.graph.triples((self.uri, None, None))))

    def triples_no_literals(self, unique_nodes=False, unique_predicates=False,  unique_subjobj=False):
        """
        return all triples in the minigraph that
        a) have the primary instance URI as subject
        b) only connect two URI references (RDF resources, not Literals)

        unique_nodes => if True, return a list of the unique nodes for these triples (excluding literals)
        unique_predicates => returns a list of only the predicates
        unique_subjobj => returns a list of only the subj/obj
        """
        if unique_nodes:
            exit = [self.uri]
            for x, y, z in self.graph.triples((self.uri, None, None)):
                if type(z) == rdflib.term.URIRef:
                    exit += [y, z]
            return list(set(exit))
        elif unique_predicates:
            exit = []
            for x, y, z in self.graph.triples((self.uri, None, None)):
                if type(z) == rdflib.term.URIRef:
                    exit += [y]
            return list(set(exit))
        elif unique_subjobj:
            exit = [self.uri]
            for x, y, z in self.graph.triples((self.uri, None, None)):
                if type(z) == rdflib.term.URIRef:
                    exit += [z]
            return list(set(exit))
        else:
            exit = []
            for x, y, z in self.graph.triples((self.uri, None, None)):
                if type(z) == rdflib.term.URIRef:
                    exit += [(x, y, z)]
            return sorted(exit)


    def list_unique_nodes(self):
        """
        wrapper for .triples(unique_nodes=True) so that it can be called from templates
        """
        return self.triples(unique_nodes=True)


    def list_unique_uris(self):
        """
        wrapper for .triples_no_literals(unique_nodes=True) so that it can be called from templates
        """
        return self.triples_no_literals(unique_nodes=True)


    def list_unique_predicates_uris(self):
        """
        wrapper for .triples(unique_predicates=True) so that it can be called from templates
        """
        return self.triples_no_literals(unique_predicates=True)

    def list_unique_subobj_uris(self):
        """
        wrapper for .triples(unique_subjobj=True) so that it can be called from templates
        """
        return self.triples_no_literals(unique_subjobj=True)
