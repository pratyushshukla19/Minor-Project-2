# Perform semantic search using and (inverse) semantic index
# on NTCIR arXiv (astro-ph) or Wikipedia (MathIR task) dataset respectively

#TODO include Formula Concept Database (AnnoMathTeX)

import pickle

# OPTIONS HERE!

#root_path = "E:\\MathQa/semanticsearch/"
root_path = "semanticsearch/"
subject = "astro-ph"
#subject = ""

# UTILE FUNCTIONS
# define function for dict list appending
def append_to_list_if_unique(list,item):
    if item not in list:
        list.append(item)

def append_to_dict_list(dict,key,item,unique):
    if key in dict:
        if unique:
            append_to_list_if_unique(dict[key],item)
        else:
            dict[key].append(item)
    else:
        dict[key] = []
        if unique:
            append_to_list_if_unique(dict[key],item)
        else:
            dict[key].append(item)

# OPEN CATALOGS
def get_formula_catalog(catalog):
    # open formula catalog
    catalog_filename = "modes7-12/" + catalog + "-Formula_Catalog.pkl"

    with open(root_path + catalog_filename, "rb") as f:
        Formula_Catalog = pickle.load(f)
    return Formula_Catalog

def get_identifier_semantics_catalog(inverse,multiple):
    # get Wikipedia (inverse) identifier semantics catalog (single or multiple)
    if inverse:
        mode1 = "Inverse_"
    else:
        mode1 = ""
    if multiple:
        mode2 = "_multiple"
    else:
        mode2 = "_single"

    file_path = root_path + "modes7-12/" + "Wikipedia-"\
                + mode1 + "Identifier_Semantics_Catalog" + mode2 + ".pkl"

    with open(file_path, "rb") as f:
        Identifier_Semantics_Catalog = pickle.load(f)
    return Identifier_Semantics_Catalog

# FORMULA SEARCH
def search_formulae_by_identifier_symbols(identifier_symbols,catalog):

    # open catalogs
    Formula_Catalog = get_formula_catalog(catalog=catalog)

    # find all formulae containing at least one identifier symbol from all queried names
    query_results = {}
    for formula in Formula_Catalog.items():
        found = []
        for identifier_symbol in identifier_symbols:
            if identifier_symbol in formula[1]["id"]:
                    found.append(identifier_symbol)

        if len(found) == len(identifier_symbols):
            query_results[formula[0] + " (" + formula[1]["file"] + ")"] = found

    # return query results
    return query_results

def search_formulae_by_identifier_names(identifier_names,catalog,multiple):

    # open catalogs
    Formula_Catalog = get_formula_catalog(catalog=catalog)
    Inverse_Identifier_Semantics_Catalog = get_identifier_semantics_catalog(inverse=True,multiple=multiple)

    # find all formulae containing at least one identifier symbol from all queried names
    query_results = {}
    for formula in Formula_Catalog.items():
        found = {}
        for identifier_name in identifier_names:
            identifierSymbols = Inverse_Identifier_Semantics_Catalog[identifier_name]
            for identifierSymbol in identifierSymbols:
                if identifierSymbol in formula[1]["id"]:
                    append_to_dict_list(found,identifier_name,identifierSymbol,unique=True)

        if len(found) == len(identifier_names):
            query_results[formula[0] + " (" + formula[1]["file"] + ")"] = found

    # return query results
    return query_results

# MATHQA

def search_formulae_by_identifiers(input,mode_number):

    catalogs = ["NTCIR-12_Wikipedia","NTCIR-12_arXiv" + "_" + subject]
    identifier_input_modes = ["symbols","names"]
    multiple_modes = [False,True]

    # 6 evaluation modes:
    # wikip,symbs,single if mode_number == 1
    # wikip,names,single if mode_number == 2
    # wikip,names,multiple if mode_number == 3
    # arxiv,symbs,single if mode_number == 4
    # arxiv,names,single if mode_number == 5
    # arxiv,names,multiple if mode_number == 6
    if mode_number == 1:
        mode_vector = [0, 0, 0]
    if mode_number == 2:
        mode_vector = [0, 1, 0]
    if mode_number == 3:
        mode_vector = [0, 1, 1]
    if mode_number == 4:
        mode_vector = [1, 0, 0]
    if mode_number == 5:
        mode_vector = [1, 1, 0]
    if mode_number == 6:
        mode_vector = [1, 1, 1]

    catalog=catalogs[mode_vector[0]]
    identifier_input_mode=identifier_input_modes[mode_vector[1]]
    multiple_mode=multiple_modes[mode_vector[2]]

    if identifier_input_mode == "symbols":
        query_results = \
            search_formulae_by_identifier_symbols(
            identifier_symbols=input,
            catalog=catalog
        )
    elif identifier_input_mode == "names":
        query_results = \
            search_formulae_by_identifier_names(
            identifier_names=input,
            catalog=catalog,
            multiple=multiple_mode
        )

    return query_results