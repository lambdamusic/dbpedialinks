#!/usr/bin/env python
# encoding: utf-8

#
# Based on from http://terse-words.blogspot.co.uk/2012/01/get-real-data-from-semantic-web.html
# I just added a few methods for other sparql queries, separate the conversion step from the queryset, and parametrized the format for the results set...
#
#


import sys
import time
import math
import optparse
import xml.dom.minidom


try:
    from SPARQLWrapper import SPARQLWrapper, JSON, XML, RDF, N3, BASIC
except:
    print "Error: can't find SPARQLWrapper (==> pip install rdflib)"
    sys.exit()




class SparqlHelper(object):

    """
    Object that knows how to run a sparql query.
    Results default to JSON and usually have the following format
    ('s' is the variable name used in the SPARQL query):

    In [8]: results
    Out[8]:
    {u'head': {u'vars': [u's']},
     u'results': {u'bindings': [
       {u's': {u'type': u'uri',
         u'value': u'http://ns.nature.com/subjects/occupational_toxicity'}},
       {u's': {u'type': u'uri',
         u'value': u'http://ns.nature.com/subjects/chemistry_publishing'}},  ... etc....
        ]}}


    NOTE: credentials: list of [username, psw]

    """

    def __init__(self, endpoint, prefixes={}, credentials=[], verbose=False):
        self.sparql = SPARQLWrapper(endpoint)

        if credentials:
            self.sparql.setHTTPAuth(BASIC)
            self.sparql.setCredentials(credentials[0], credentials[1])

        self.prefixes = {

            "dc" : "http://purl.org/dc/elements/1.1/" ,
            "dcterms" : "http://purl.org/dc/terms/" ,
            "owl" : "http://www.w3.org/2002/07/owl#" ,
            "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#" ,
            "rdfs" : "http://www.w3.org/2000/01/rdf-schema#" ,
            "sh" : "http://www.w3.org/ns/shacl#" ,
            "skos" : "http://www.w3.org/2004/02/skos/core#" ,
            "vann" : "http://purl.org/vocab/vann/" ,
            "void" : "http://rdfs.org/ns/void#" ,
            "xsd" : "http://www.w3.org/2001/XMLSchema#" ,
        }
        self.prefixes.update(prefixes)
        self.prefixes_statement = ["PREFIX %s: <%s>" % (k, r) for k, r in self.prefixes.iteritems()]
        self.verbose = verbose
        self.format = ""  # dynamically assigned at query time
        self.endpoint = endpoint  # just for caching it
        self.credentials = credentials



    def __getFormat(self, format):
        """
        Defaults to JSON  [ps: 'RDF' is the native rdflib representation]
        https://github.com/RDFLib/sparqlwrapper/blob/master/scripts/example.py
        """
        if format == "XML":
            self.sparql.setReturnFormat(XML)
            self.format = "XML"
        elif format == "RDF":
            self.sparql.setReturnFormat(RDF)
            self.format = "RDF"
        elif format == "N3":
            self.sparql.setReturnFormat(N3)
            self.format = "N3"
        else:
            self.sparql.setReturnFormat(JSON)
            self.format = "JSON"


    def __doQuery(self, query, format, convert):
        """
        Inner method that does the actual query
        """
        self.__getFormat(format)
        self.sparql.setQuery(query)
        try:
            if convert:
                results = self.sparql.query().convert()
            else:
                results = self.sparql.query()
        except Exception, e:
            print >> sys.stderr, 'ERROR WITH SPARQL QUERY:\n', e
            raise

        return results




    # Query Wrappers
    # --------------

    def query(self, q, format="", convert=True):
        """
        Generic QUERY structure. 'q' is the main body of the query.

        The results passed out are not converted yet: see the 'format' method
        Results could be iterated using the idiom: for l in obj : do_something_with_line(l)

        If convert is False, we return the collection of rdflib instances

        """

        lines = self.prefixes_statement[:]

        lines.extend(q.split("\n"))
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"

        return self.__doQuery(query, format, convert)



    def describe(self, uri, format="", convert=True):
        """
        A simple DESCRIBE query with no 'where' arguments. 'uri' is the resource you want to describe.

        See also:
        https://www.w3.org/TR/sparql11-query/#describe

        NOTE: describe queries return results only as N3 text (in GraphDB) eg:

        ..'<http://name.scigraph.com/ontologies/core/> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Thing> .\n<http://name.scigraph.com/ontologies/core/> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Ontology> .\n<http://name.scigraph.com/ontologies/core/> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ....

        Also, DESCRIBE returns triples with URI as subject and triples with URI as OBJECT, so potentially many unwanted results!

        """
        lines = self.prefixes_statement[:]

        if uri.startswith("http://"):
            lines.extend(["DESCRIBE <%s>" % uri])
        else:  # it's a shortened uri
            lines.extend(["DESCRIBE %s" % uri])
        query = "\n".join(lines)


        if self.verbose:
            print query, "\n\n"

        return self.__doQuery(query, format, convert)




    def uri_triples(self, uri, format="", convert=True):
        """
        Get all triples for a URI TODO: expand with union where URI is both predicate and object

        2016-10-07: using a construct so to facilitate serializing
        """

        lines = self.prefixes_statement[:]

        q =  """
            CONSTRUCT {?subject ?predicate ?object}
            WHERE {
            bind (<%s> as ?subject) .
            ?subject ?predicate ?object .
            }""" % uri

        lines.extend([q])
        query = "\n".join(lines)


        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)


    def uri_instances(self, uri, format="", convert=True, limit=500):
        """
        Try to get instances for a URI
        2016-10-12: TRYING TO MAKE IT BETTER< NOT ENOUGH TIME TO TEST IT

        """

        lines = self.prefixes_statement[:]

        q =  """
SELECT DISTINCT ?uri ?label WHERE {
    bind (<%s> as ?class) .
    ?uri a ?class .
            {?uri sg:publishedName ?label . }
    UNION   {?uri sg:title ?label . }
    UNION   {?uri rdfs:label ?label . }
    UNION   {?uri skos:prefLabel ?label . }
    UNION   {?uri rdf:comment ?label . }
    UNION   {?uri sg:title ?label . }
}
    limit %d""" % (uri, limit)

        lines.extend([q])
        query = "\n".join(lines)


        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)



    def ontology(self, format="", convert=True):
        """
        Get all entities of type owl:Class
        """

        lines = self.prefixes_statement[:]

        q =  """
            SELECT *
            WHERE { ?class a owl:Class }"""

        lines.extend([q])
        query = "\n".join(lines)


        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)



    def class_stats(self, format="", convert=True):

        lines = self.prefixes_statement[:]

        q = """select distinct ?entity (COUNT (?p) as ?count)
                    where
                    {?p a ?entity}
                    GROUP BY ?entity
                    ORDER BY DESC(?count)
                    """

        lines.extend([q])
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)



    def instances_count(self, resource_uri, format="", convert=True):
        """
        note: this returns a dict eg
        {u'head': {u'vars': [u'count']}, u'results': {u'bindings': [{u'count': {u'datatype': u'http://www.w3.org/2001/XMLSchema#integer', u'type': u'literal', u'value': u'2989'}}]}}
        """

        lines = self.prefixes_statement[:]

        q = """select (COUNT (?p) as ?count)
                    where
                    {?p a <%s>}
                    """ % resource_uri

        lines.extend([q])
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)

    def search_labels(self, stringa, format="", convert=True):

        lines = self.prefixes_statement[:]

        q =  """
            SELECT *
            WHERE {     ?uri rdfs:label ?label .
                         FILTER contains(LCASE(?label), "%s")
                }"""  % stringa

        lines.extend([q])
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)



    def search_scigraph_entity(self, stringa, entity_qname, format="", convert=True):
        """
        search instances of a selected entity for a string value.
        Using only short string fields e.g. title or label
        """

        lines = self.prefixes_statement[:]

        q =  """

SELECT DISTINCT ?uri ?label
WHERE {
    BIND ("%s" as ?stringa) .
    BIND (%s as ?entity) .
    {
            ?uri a ?entity .
            ?uri skos:prefLabel ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {
            ?uri a ?entity .
            ?uri sg:title ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {
            ?uri a ?entity .
            ?uri rdfs:label ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
} LIMIT 50

            """  % (stringa, entity_qname)

        lines.extend([q])
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)



    def search_scigraph_labels(self, stringa, format="", convert=True):
        """
        search over short string fields (no DOIs)
        """

        lines = self.prefixes_statement[:]

        q =  """

SELECT DISTINCT ?uri ?label
WHERE {
    BIND ("%s" as ?stringa) .
    {
            ?uri skos:prefLabel ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {
            ?uri sg:title ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri rdfs:label ?label .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri rdfs:comment ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri skos:definition ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
} LIMIT 500

            """  % stringa

        lines.extend([q])
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)




    def search_all_descs(self, stringa, format="", convert=True):

        lines = self.prefixes_statement[:]

        q =  """

SELECT DISTINCT ?uri ?label
WHERE {
    BIND ("%s" as ?stringa) .
    {
            ?uri skos:prefLabel ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {
            ?uri sg:title ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri rdfs:label ?label .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri rdfs:comment ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri skos:definition ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
    UNION
    {

            ?uri sg:doi ?label  .
            FILTER contains(LCASE(?label), ?stringa)

    }
} LIMIT 1000

            """  % stringa

        lines.extend([q])
        query = "\n".join(lines)

        if self.verbose:
            print query, "\n\n"


        return self.__doQuery(query, format, convert)












def parse_options():
    """
    @TODO: update

    parse_options() -> opts, args

    Parse any command-line options given returning both
    the parsed options and arguments.
    """

    parser = optparse.OptionParser(usage=USAGE, version=VERSION)

    parser.add_option("-q", "--query",
            action="store", type="string", default="", dest="query",
            help="SPARQL query string")

    parser.add_option("-f", "--format",
            action="store", type="string", default="JSON", dest="format",
            help="Results format: one of JSON, XML")

    parser.add_option("-d", "--describe",
            action="store", type="string", default="", dest="describe",
            help="Describe Query: just pass a URI")

    parser.add_option("-a", "--alltriples",
            action="store", type="string", default="", dest="alltriples",
            help="Get all available triples for a URI")

    parser.add_option("-o", "--ontology",
            action="store_true", default=False, dest="ontology",
            help="Get all entities of type owl:Class - aka the ontology")

    opts, args = parser.parse_args()

    if len(args) < 1 and not (opts.query or opts.describe or opts.alltriples or opts.ontology):
        parser.print_help()
        raise SystemExit, 1

    return opts, args





def main():
    # get parameters
    opts, args = parse_options()
    url = args[0]
    query, format, describe, alltriples, ontology = opts.query, opts.format, opts.describe, opts.alltriples, opts.ontology

    sTime = time.time()

    s = SparqlHelper(url)

    if query:
        print "Contacting %s ... \nQuery: \"%s\"; Format: %s\n" % (url, query, format)
        results = s.query(query, format)
    elif describe:
        print "Contacting %s ... \nQuery: DESCRIBE %s; Format: %s\n" % (url, describe, format)
        results = s.describe(describe, format)
    elif alltriples:
        print "Contacting %s ... \nQuery: ALL TRIPLES FOR %s; Format: %s\n" % (url, alltriples, format)
        results = s.allTriplesForURI(alltriples, format)
    elif ontology:
        print "Contacting %s ... \nQuery: ONTOLOGY; Format: %s\n" % (url, format)
        results = s.ontology(format)


    if format == "JSON":
        results = results["results"]["bindings"]
        for d in results:
            for k, v in d.iteritems():
                print "[%s] %s=> %s" % (k, v['type'],v['value'])
            print "----"
    elif format == "XML":
        print results.toxml()
    else:
        print results




    # print some stats....
    eTime = time.time()
    tTime = eTime - sTime
    print "-" * 10
    print "Time:       %0.2fs" %  tTime

    try:
        # most prob this works only with JSON results, but you get the idea!
        print "Found:      %d" % len(results)
        print "Stats:      (%d/s after %0.2fs)" % (
                  int(math.ceil(float(len(results)) / tTime)), tTime)
    except:
        pass

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
