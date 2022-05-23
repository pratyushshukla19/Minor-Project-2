import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
import json
from semanticsearch.SemanticSearch_Wikidata_mathqa import get_formula_qid

#---------
#PYWIKIBOT
#---------

def retrieve_identifier_properties(FormulaName):

    #retrieve Wikidata page item
    identifiers = dict()
    try:
        try: #without qid
            site = pywikibot.Site("en", "wikipedia")
            page = pywikibot.Page(site, FormulaName)
            item = pywikibot.ItemPage.fromPage(page)
        except: #with qid
            qid = get_formula_qid(FormulaName)
            site = pywikibot.Site("wikidata", "wikidata")
            repo = site.data_repository()
            item = pywikibot.ItemPage(repo, qid)

        #formulaQID = str(item).replace("[[wikidata:", '').replace("]]", '')
        #formula_string = item.claims['P2534'][0].getTarget()

        #retrieve identifiers
        try:
            identifier_list = item.claims['P527'] # P527: 'has part'
        except:
            identifier_list = item.claims['P4935'] # P435: 'calculated from'
        # catch values
        identifier_symbol = ""
        identifier_name = ""
        identifier_value = ""
        print("Successfully retrieved identifier properties from Wikidata")
        for identifier in identifier_list:
            print("Processing identifier " + str(identifier))
            def query_part_target(identifier,property_list):
                for property in property_list:
                    try:
                        return identifier.qualifiers[property][0].target
                    except:
                        pass
                return ""

            identifier_symbol = query_part_target(identifier,['P2534','P416','P7973','P2534']) #list of possible identifier properties
            print("Identifier symbol: " + identifier_symbol)
            identifier_name = str(identifier.getTarget().text['labels']['en'])
            print("Identifier name: " + identifier_name)

            identifiers[identifier_symbol] = {}
            identifiers[identifier_symbol]['name'] = identifier_name
            try:
                identifier_value = str(identifier.getTarget().claims['P1181'][0].getTarget().amount)
                print("Identifier value: " + identifier_value)
                identifiers[identifier_symbol]['value'] = identifier_value
            except:
                pass
        return identifiers

    except:
        print("Could not retrieve identifier properties")
        return dict()

#------
#SPARQL
#------

def retrieve_identifier_name(formulaQID,identifierSymbol):

    try:
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery("""#find identifier name
        SELECT ?identifierLabel WHERE {
        wd:""" + formulaQID + """ p:P527 ?statement. #p: points to statement node
        ?statement ps:P527 ?identifier. #ps: property statement
        ?statement pq:P2534 ?symbol. #ps: property qualifier
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        FILTER(CONTAINS(STR(?symbol), '<mi>""" + identifierSymbol + """</mi>'))
        }""")
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        tmp_results = []
        for result in results["results"]["bindings"]:
            tmp_results.append(result)

        json_str = json.dumps(tmp_results[0])
        resp = json.loads(json_str)
        return resp['identifierLabel']['value']

    except:
        return ""
    
def retrieve_identifier_value(formulaQID,identifierSymbol):

    try:
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery("""#find identifier value
        SELECT ?value WHERE {
        wd:""" + formulaQID + """ wdt:P527 ?identifier.
        ?identifier wdt:P416 ?symbol.
        ?identifier wdt:P1181 ?value.
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        FILTER(STR(?symbol) = '""" + identifierSymbol + """')
        }""")
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        tmp_results = []
        for result in results["results"]["bindings"]:
            tmp_results.append(result)

        json_str = json.dumps(tmp_results[0])
        resp = json.loads(json_str)
        return resp['value']['value']

    except:
        return ""