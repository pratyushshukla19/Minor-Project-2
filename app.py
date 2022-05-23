import json
import os
import re

from flask import Flask
from flask import render_template
from flask import request
from flask.json import jsonify
from flask_cors import CORS
from ppp_datamodel import Sentence
from sympy import Symbol
from sympy.core.sympify import sympify
from sympy.parsing.latex import parse_latex

import getidentifiers
import latexformlaidentifiers

# identifier symbol retrieval
from semanticsearch.IdentifierSemantics import get_identifier_symbol
from semanticsearch.SemanticSearch_Wikidata_mathqa import get_formula_qid

# semantic search using arXiv or Wikipedia index
from semanticsearch.SemanticSearch_arXivWikipedia_mathqa import get_identifier_semantics_catalog,search_formulae_by_identifiers
# semantic search using Wikidata SPARQL query
from semanticsearch.SemanticSearch_Wikidata_mathqa import search_formulae_by_identifiers_Wikidata,search_formulae_by_concept_name_Wikidata

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parentdir)
os.environ['PPP_QUESTIONPARSING_GRAMMATICAL_CONFIG'] = os.path.dirname(
    os.path.abspath(__file__)) + '/example_config.json'
os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = '1'
# os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.abspath(__file__)) + '/pywikibot'
from ppp_datamodel.communication import Request
from ppp_questionparsing_grammatical import RequestHandler
from getformula import get_formula
from getformula import FormulaRequestHandler
from getformula import HindiRequestHandler
from latexformlaidentifiers import Formulacalculation

from identifier_properties import retrieve_identifier_properties
# from identifier_properties import retrieve_identifier_name
# from identifier_properties import retrieve_identifier_value

import traceback

# get input from question (identifier symbols / relationships)
def get_input(question,exclude):
    input = []
    candidates = question.split()
    for word in candidates:
        if "?" in word:
            word = word.strip("?")
        if not word in exclude and len(word) > 0:
            input.append(word)
    return input

show_single_identifier_names = True

def getlhsrhs(formula, ext):
    """
        Break the formula into lhs and rhs
    """
    lhs, rhs = formula.split(ext, 1)
    return lhs,rhs


def makeidentifier(symbol, values):
    """
        Make dictionary for Values of Symbol
    """
    symvalue = {}
    for i in symbol:
        for j in values:
            if i == Symbol(j):
                value = values[j]
                symvalue[i] = value

    return symvalue


def makeresponse(formul,subject,mode,datasource):
    """
        Make response for the API
    """
    try:
        # TODO: unbreak for english
        #subject = req.subject
        reques = Formulacalculation(formul)
        identifiers = reques.answer()

        # todo: build identifier value output
        if identifiers is not None:
            listidentifiers = list(identifiers)

            responselist = []
            valuelist = []
            # item = identifier
            identifier_properties = retrieve_identifier_properties(subject)
            for item in listidentifiers:
                try:
                    # symbol question
                    if mode == 'symbol_question':
                        name = " (" + subject + ")"
                    # if relationship_question:
                    #
                    #     if show_single_identifier_names:
                    #         # single identifier name
                    #         inv_sem_idx = get_identifier_semantics_catalog(inverse=False,multiple=False)
                    #         name = " (" + inv_sem_idx[str(item)[0]] + ")"
                    #
                    #     if not show_single_identifier_names:
                    #         # multiple identifier names
                    #         inv_sem_idx = get_identifier_semantics_catalog(inverse=False, multiple=True)
                    #         name = " (" + str(inv_sem_idx[str(item)[0]]) + ")"
                    #         # only the first symbol is the identifier (the others may be sub- oder superscripts)
                    #
                    else:
                        name = " (" + identifier_properties[str(item)]['name'] + ")"

                except:
                    name = ""
                try:
                    valuelist.append(identifier_properties[str(item)]['value'])
                except:
                    valuelist.append("Enter value")

                # responselist.append(str(item))
                responselist.append(str(item) + name)

            # get qid
            try:
                qid = get_formula_qid(subject)
            except:
                qid = ""

            responselist.append(dict(formula=formul))
            responselist.append(dict(values=valuelist))
            responselist.append(dict(qid=qid,datasource=datasource))
            #responselist.append(dict(datasource=datasource))
            #json_data = json.dumps(responselist)
            response = jsonify(responselist)
            # json_data2 = json.dumps(valuelist)
            # response.values = jsonify(valuelist)
            response.status_code = 200
            return response
        else:
            response = jsonify(formul)
            response.status_code = 206
            print(response)
            return response

    except:
        response = jsonify("System is not able to find the result.")
        response.status_code = 202
        return response


# OUT: response

app = Flask(__name__)
CORS(app)


@app.route('/')
def my_form():
    return render_template("index.html")


@app.route('/getresponse', methods=['POST'])
def my_form_post():
    """
        Get formula from the user input and process it
        Return response
    """
    try:
        if request.form['formula']:
            global formula
            formula = request.form['formula']
            global processedformula
            processedformula = latexformlaidentifiers.prepformula(formula)

            if formula is not None:
                return makeresponse(processedformula,None,None,'Wikidata')

    # except:
    #     response= jsonify("System is not able to find the result.")
    #     response.status_code = 202
    #     return response

    except Exception as ex:
        print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))


@app.route('/getengformula', methods=['POST'])
def get_formula():
    """
        Get English question from the user parse it to Questionparsing module to get Triple
        Parse Triple (Subject, predicate, ?) to FormulaRequestHandler to get Formula from Wikidata
        Return response
    """

    # parse question
    try:
        question = request.form['formula']
        # lowercase first letter of question
        question = question[:1].lower() + question[1:]
        print("Question: " + question)

        # Determine question type

        # identifier symbol question
        if "symbol" in question:
            mode = 'symbol_question'
            print("Symbol question")

            exclude = ["what", "is", "the", "symbol", "for", "?"]
            subject = get_input(question,exclude)

            formula = get_identifier_symbol(identifier_name=subject)

        # relationship question (semantic search)
        elif "relationship" in question or "relation" in question:
            mode = 'relationship_question'
            print("Relationship question")

            exclude = ["what","is","the","relationship","relation","between","and","?"]
            input = get_input(question,exclude)

            # check if input is identifier names or symbols
            # symbols if all characters
            #
            #symbols = True
            #for element in input:
            #    if len(element) > 1:
            #        symbols = False
            # names if at least one is word
            #if symbols:
            #    mode_number = 1
            #else:
            #    mode_number = 2
            #
            # results = search_formulae_by_identifier_names\
            #     (identifier_names=identifier_names,catalog="NTCIR-12_arXiv_astro-ph"\
            #      ,inverse=True,multiple=False)
            #results = search_formulae_by_identifiers(input=input,
            #                                                mode_number=mode_number)
            formula,subject = search_formulae_by_identifiers_Wikidata(identifiers=input)
            #formula = list(results.items())[0][0].split(" (")[0]

        # Formula question
        elif "formula" in question:
            mode = 'formula_question'
            print("Formula question")

            exclude = ["what ", "is ", "the ", "formula ", "for ", "?"]
            for word in exclude:
                question = question.replace(word,"")
            # strip whitespace (at beginning) and end
            #subject = question[1:].strip()
            subject = question.strip()

            formula,datasource = search_formulae_by_concept_name_Wikidata(subject)

        # General or geometry question
        else:
            mode = 'general_geometry'
            print("General or geometry question")
            meas = {'accuracy': 0.5, 'relevance': 0.5}
            q = RequestHandler(Request(language="en", id=1, tree=Sentence(question), measures=meas))
            try:
                query = q.answer()
            except:
                print("Stanford CoreNLP was unable to parse the question")
            reques = FormulaRequestHandler(query)

            subject = reques.request[0]._attributes['tree']._attributes['subject']._attributes['value']

            formula = reques.answer()
            formula = latexformlaidentifiers.prepformula(formula)

        # generate response
        if not (formula.startswith("System")):
            try:
                datasource = datasource
            except:
                datasource = 'Wikidata'
            return makeresponse(formula,subject,mode,datasource)
        else:
            response = jsonify(formula)
            response.status_code = 202
            print(response)
            return response

    except Exception :
            response= jsonify("System is not able to find the result.")
            response.status_code = 202
            return response
            #return ("System is not able to find the result.")

    # except Exception as ex:
    #     print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))


@app.route('/gethindiformula', methods=['POST'])
def get_hindiformula():
    """
        Get Hindi question from the user and apply regex to get subject and predicate
        Parse subject and predicate to HindiRequestHandler to get formula
        Return response
    """

    try:
        question = request.form['formula']
        matchObj = re.match(r'(.*)की (.*?) .*', question, re.M | re.I)
        matchObj1 = re.match(r'(.*)के लिए (.*?) क्या है *', question, re.M | re.I)
        matchObj2 = re.match(r'(.*)और (.*?) के बीच *', question, re.M | re.I)
        if matchObj:
            subject = matchObj.group(1)
            predicate = matchObj.group(2)

        if matchObj1:
            subject = matchObj1.group(1)
            predicate = matchObj1.group(2)

        if matchObj2:
            subject = matchObj2.group(1)
            predicate = matchObj2.group(2)

        reques = HindiRequestHandler("hi", subject, predicate)
        global formula
        formula = reques.answer()
        global processedformula
        processedformula = latexformlaidentifiers.prepformula(formula)
        print(processedformula)
        if not (formula.startswith("System")):
            return makeresponse(processedformula,None,None,'Wikidata')
        else:
            response = jsonify(formula)
            response.status_code = 202
            return response
    except Exception:
        response = jsonify("System is not able to find the result.")
        response.status_code = 202
        return response


@app.route('/getfinalresult', methods=['POST'])
def my_form_json():
    """
        Get Values for the identifiers
        Return Calculated result 
    """

    try:
        result = json.loads(request.data.decode('utf8'))
        formula = result['formula']
        del result['formula']
        identifiers_dict = result

        # slice off identifier names for calculation
        symbolvalue = {}
        for identifier in identifiers_dict.items():
            try:
                symbol = identifier[0].split(" (")[0]
                value = identifier[1]
                symbolvalue[symbol] = value
            except:
                pass

        # remove displaystyle
        formula = formula.replace("\\displaystyle","")

        # formula parsing and calculation
        seprator = getidentifiers.formuladivision(formula)
        if seprator is not None:
            lhs, rhs = getlhsrhs(formula, seprator)
            f = parse_latex(rhs)
            f1 = parse_latex(lhs)
            latexlhs = sympify(f1)
            l = sympify(f)
            # print(l)
            #symbolvalue = makeidentifier(identifier, identifiers_dict)
            value = l.evalf(subs=symbolvalue)

            return ("%s %s %.2e" % (latexlhs, seprator, value))
        else:
            l = sympify(formula)
            value = l.evalf(subs=identifiers_dict)

            return ("%.2e" % value)

    except Exception:
        return ("System is not able to find the result.")


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
    # get_formula()
