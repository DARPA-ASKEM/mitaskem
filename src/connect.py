import asyncio
import io
import json
import os
import re
import pandas as pd
from cryptography.fernet import Fernet
import openai
from openai import OpenAIError
from PIL import Image
import gpt_interaction
from tqdm import tqdm
import ast
import sys

from util import *
from gpt_interaction import *
from mira_dkg_interface import *
from gpt_key import *
# from automates.program_analysis.JSON2GroMEt.json2gromet import json_to_gromet
# from automates.gromet.query import query

def index_text_path(text_path: str) -> str:
    fw = open(text_path + "_idx", "w")
    with open(text_path) as fp:
        for i, line in enumerate(fp):
            fw.write('%d\t%s' % (i, line))
    fw.close()
    return text_path + "_idx"

def index_text(text: str) -> str:
    idx_text = ""
    tlist = text.split('\n')
    # print(tlist)
    for i, line in enumerate(tlist):
        if i==len(tlist)-1 and line== "":
            break
        idx_text = idx_text + ('%d\t%s\n' % (i, line))
    return idx_text




def get_gpt_match(prompt, key, model="text-davinci-002"):
    # mykey = b'Z1QFxceGL_s6karbgfNFyuOdQ__m5TfHR7kuLPJChgs='
    # enc = b'gAAAAABjRh0iNbsVb6_DKSHPmlg3jc4svMDEmKuYd-DcoTxEbESYI9F8tm8anjbsTsZYHz_avZudJDBdOXSHYZqKmhdoBcJd919hCffSMg6WFYP12hpvI7EeNppGFNoZsLGnDM5d6AOUeRVeIc2FbmB_j0vvcIwuEQ=='
    # fernet = Fernet(mykey)
    # openai.api_key = fernet.decrypt(enc).decode()
    openai.api_key = key
    response = openai.Completion.create(model=model, prompt=prompt, temperature=0.0, max_tokens=256)
    result = response.choices[0].text.strip()
    # print(result)
    return result


def read_text_from_file(text_path):
    text_file = open(text_path, "r")
    prompt = text_file.read()
    return prompt


# Get gpt-3 prompt with variables, ontology terms and match targets
def get_prompt(vars, terms, target):
    text_file = open("prompts/prompt.txt", "r")
    prompt = text_file.read()
    text_file.close()

    vstr = ''
    vlen = len(vars)
    i = 1;
    for v in vars:
        vstr += str(i) + " (" + str(v[1]) + ", " + str(v[2]) + ")\n"
        i += 1;
    # print(vstr)
    tstr = '[' + ', '.join(terms) + ']'
    tlen = len(terms)
    # print(tstr)
    prompt = prompt.replace("[VAR]", vstr)
    prompt = prompt.replace("[VLEN]", str(vlen))
    prompt = prompt.replace("[TERMS]", tstr)
    prompt = prompt.replace("[TLEN]", str(tlen))
    prompt = prompt.replace("[TARGET]", target)
    # print(prompt)
    return prompt


# Get gpt-3 prompt with formula, code terms and match formula targets
def get_code_formula_prompt(code, formula, target):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/code_formula_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[CODE]", code)
    prompt = prompt.replace("[FORMULA]", formula)
    prompt = prompt.replace("[TARGET]", target)
    # print(prompt)
    return prompt


# Get gpt-3 prompt with variable and datasets, and match variable target with the best data columns
def get_var_dataset_prompt(vars, dataset, target):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/var_dataset_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[DESC]", vars)
    prompt = prompt.replace("[DATASET]", dataset)
    prompt = prompt.replace("[TARGET]", target)
    # print(prompt)
    return prompt


# Get gpt-3 prompt with formula, and match variable targets
def get_var_formula_prompt(desc, var):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/var_formula_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[DESC]", desc)
    prompt = prompt.replace("[TARGET]", var)
    # print(prompt)
    return prompt

# Get gpt-3 prompt with formula, and match variable targets
def get_formula_var_prompt(formula):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/formula_var_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[FORMULA]", formula)
    # print(prompt)
    return prompt

def get_all_desc_formula_prompt(all_dsec, latex_var):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/all_desc_formula_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[DESC]", all_dsec)
    prompt = prompt.replace("[TARGET]", latex_var)
    return prompt

# Get gpt-3 prompt with formula, code terms and match formula targets
def get_code_text_prompt(code, text, target):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/code_text_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[CODE]", code)
    prompt = prompt.replace("[TEXT]", text)
    prompt = prompt.replace("[TARGET]", target)
    # print(prompt)
    return prompt

def get_text_param_prompt(text):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/text_param_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[TEXT]", text)
    return prompt

def get_text_var_prompt(text):
    text_file = open(os.path.join(os.path.dirname(__file__), 'prompts/text_var_prompt.txt'), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[TEXT]", text)
    return prompt


# Get gpt-3 prompt with code, dataset and match function targets
def get_code_dataset_prompt(code, dataset, target):
    text_file = open(os.path.join(os.path.dirname(__file__), "prompts/code_dataset_prompt.txt"), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[CODE]", code)
    prompt = prompt.replace("[DATASET]", dataset)
    prompt = prompt.replace("[TARGET]", target)
    # print(prompt)
    return prompt

def get_text_column_prompt(text, column):
    text_file = open(os.path.join(os.path.dirname(__file__), "prompts/text_column_prompt.txt"), "r")
    prompt = text_file.read()
    text_file.close()

    prompt = prompt.replace("[TEXT]", text)
    prompt = prompt.replace("[COLUMN]", column)

    return prompt



def get_variables(path):
    list = []
    with open(path) as myFile:
        for num, line in enumerate(myFile, 1):
            match = re.match(r'\s*(\S+)\s*=\s*([-+]?(?:\d*\.\d+|\d+))\s*', line)
            if match:
                para = match.group(1)
                val = match.group(2)
                # print(num, ",", para, ",", val)
                list.append((num, para, val))
    print("Extracted variables: ", list)
    return list

def match_code_targets(targets, code_path, terms):
    vars = get_variables(code_path)
    vdict = {}
    connection = []
    for idx, v in enumerate(vars):
        vdict[v[1]] = idx
    for t in targets:
        val = get_match(vars, terms, t)
        connection.append((t, {val: "grometSubObject"}, float(vars[vdict[val]][2]), vars[vdict[val]][0]))
    return connection


def ontology_code_connection():
    terms = ['population', 'doubling time', 'recovery time', 'infectious time']
    code = "model/SIR/CHIME_SIR_while_loop.py"
    targets = ['population', 'infectious time']
    val = []
    try:
        val = match_code_targets(targets, code, terms)
    except OpenAIError as err:
        print("OpenAI connection error:", err)
        print("Using hard-coded connections")
        val = [("infectious time", {"name": "grometSubObject"}, 14.0, 67),
               ("population", {"name": "grometSubObject"}, 1000, 80)]
    print(val)



def code_text_connection(code, text, gpt_key, interactive = False):
    code_str = code
    idx_text = index_text(text)
    tlist = text.split("\n")
    targets = extract_func_names(code_str)
    print(f"TARGETS: {targets}")
    tups = []
    try:
        for t in targets:
            prompt = get_code_text_prompt(code_str, idx_text, t)
            match = get_gpt_match(prompt, gpt_key)
            ilist = extract_ints(match)
            ret_s = select_text(tlist, int(ilist[0]), int(ilist[-1]), 1, interactive)
            if interactive: 
                print("Best description for python function {} is in lines {}-{}:".format(t, ilist[0], ilist[-1]))
                print(ret_s)
                print("---------------------------------------")
            else:
                tups.append((t, int(ilist[0]), int(ilist[-1]), ret_s))
        return tups, True
    except OpenAIError as err:
        if interactive:
            print("OpenAI connection error:", err)
        else:
            return f"OpenAI connection error: {err}", False


def code_dataset_connection(code, schema, gpt_key, interactive=False):
    targets = extract_func_names(code)
    tups = []
    try:
        for t in targets:
            prompt = get_code_dataset_prompt(code, schema, t)
            match = get_gpt_match(prompt, gpt_key)
            returnable = match.split("function are the ")[1].split(" columns.")[0].split(" and ")

            if interactive:
                print(returnable)
                print("---------------------------------------")
            else:
                tups.append((t, returnable))
        return tups, True
    except OpenAIError as err:
        if interactive:
            print("OpenAI connection error:", err)
        else:
            return f"OpenAI connection error: {err}",False

def text_column_connection(text, column, gpt_key):
    try:
        prompt = get_text_column_prompt(text, column)
        match = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
        return match, True
    except OpenAIError as err:
        return f"OpenAI connection error: {err}",False


def select_text(lines, s, t, buffer, interactive=True):
    ret_s = ""
    start = s - buffer
    end = t + buffer
    if start < 0:
        start = 0
    if end >= len(lines):
        end = len(lines) - 1
    for i in range(start, end+1):
        if i<=t and i>=s:
            if interactive:
                ret_s += ">>\t{}\t{}".format(i,lines[i])
            else:
                ret_s += lines[i]
        elif interactive:
            ret_s += "\t{}\t{}".format(i, lines[i])
    return ret_s

def code_formula_connection(code, formulas, gpt_key):
    flist = formulas.split("\n")
    matches = []
    if flist[-1]=="":
        del flist[-1]
    try:
        for t in flist:
            prompt = get_code_formula_prompt(code, formulas, t)
            match = get_gpt_match(prompt, gpt_key)

            matches.append([t, match.split(":")[1]])
        return matches, True
    except OpenAIError as err:
        return f"OpenAI connection error: {err}", False


def vars_dataset_connection(json_str, formula, gpt_key):
    json_list = ast.literal_eval(json_str)

    var_list = list(filter(lambda x: x["type"] == "variable", json_list))

    prompt = get_formula_var_prompt(formula)
    latex_vars = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
    latex_vars = latex_vars.split(':')[1].split(',')

    latex_var_set = {}

    all_desc_ls = [var['name'] for var in var_list]
    all_desc = '\n'.join(all_desc_ls)

    try:
        for latex_var in tqdm(latex_vars):
            prompt = get_all_desc_formula_prompt(all_desc, latex_var)
            ans = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
            ans = ans.split('\n')

            matches = []
            for a in ans:
                if a in all_desc_ls:
                    a_idx = all_desc_ls.index(a)
                    matches.append(var_list[a_idx]['id'])
            latex_var_set[latex_var] = matches

        matches_str = ",".join(
            [("\"" + var + "\" : [\"" + "\",\"".join([str(item) for item in latex_var_set[var]]) + "\"]") for var in
             latex_var_set])

        s = ", {\"type\":\"equation\", \"latex\":" + formula + \
            ", \"id\":\"e" + str(hash(formula) % ((sys.maxsize + 1) * 2)) + \
            "\", \"matches\": {" + matches_str + "} }]"

        new_json_str = json_str[:-1] + s

        return new_json_str, True
    except OpenAIError as err:
        return f"OpenAI connection error: {err}", False


def vars_dataset_connection(json_str, dataset, gpt_key):
    json_list = ast.literal_eval(json_str)

    var_list = list(filter(lambda x: x["type"] == "variable", json_list))

    all_desc_ls = [(var['name']+": "+var['text_annotations'][0]) for var in var_list]
    all_desc = '\n'.join(all_desc_ls)

    all_vs = [var['name'] for var in var_list]

    vs_data = {}

    try:
        for target in tqdm(all_vs):
            a_idx = all_vs.index(target)
            prompt = get_var_dataset_prompt(all_desc, dataset, all_desc_ls[a_idx])
            ans = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
            ans = ans.split('\n')
            vs_data[var_list[a_idx]['id']] = ans

        matches_str = ",".join(
            [("\"" + var + "\":[\"" + "\",\"".join([str(item) for item in vs_data[var]]) + "\"]") for var in
             vs_data])

        s = ", {\"type\":\"datasetmap\""+ \
            ", \"id\":\"e" + str(hash(matches_str) % ((sys.maxsize + 1) * 2)) + \
            "\", \"matches\": " + json.dumps(vs_data) + " }]"

        new_json_str = json_str[:-1] + s

        return new_json_str, True
    except OpenAIError as err:
        return f"OpenAI connection error: {err}", False

def vars_formula_connection(json_str, formula, gpt_key):
    json_list = ast.literal_eval(json_str)
    
    var_list = list(filter(lambda x: x["type"] == "variable", json_list))

    prompt = get_formula_var_prompt(formula)
    latex_vars = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
    latex_vars = latex_vars.split(':')[1].split(',')

    latex_var_set = {}

    all_desc_ls = [var['name'] for var in var_list]
    all_desc = '\n'.join(all_desc_ls)

    try:
        for latex_var in tqdm(latex_vars):
            prompt = get_all_desc_formula_prompt(all_desc, latex_var)
            ans = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
            ans = ans.split('\n')

            matches = []
            for a in ans:
                if a in all_desc_ls:
                    a_idx = all_desc_ls.index(a)
                    matches.append(var_list[a_idx]['id'])
            latex_var_set[latex_var] = matches

            # for desc in tqdm(var_list):
            #     prompt = get_var_formula_prompt(desc["name"], latex_var)
            #     ans = get_gpt_match(prompt, gpt_key, model="text-davinci-003")
            #     ans = ans.split(':')[1]


            #     if ans == 'YES':
            #         current_matches = latex_var_set.get(latex_var, [])
            #         current_matches.append(desc["id"])
            #         latex_var_set[latex_var] = current_matches
                    

        matches_str = ",".join([("\"" + var + "\" : [\"" + "\",\"".join([str(item) for item in latex_var_set[var]]) + "\"]") for var in latex_var_set])

        s = ", {\"type\":\"equation\", \"latex\":" + formula + \
            ", \"id\":\"e" + str(hash(formula)%((sys.maxsize + 1) * 2))+\
            "\", \"matches\": {" + matches_str + "} }]"

        new_json_str = json_str[:-1] + s

        return new_json_str, True
    except OpenAIError as err:
        return f"OpenAI connection error: {err}", False

DEFAULT_TERMS = ['population', 'doubling time', 'recovery time', 'infectious time']
DEFAULT_ATTRIBS = ['description', 'synonyms', 'xrefs', 'suggested_unit', 'suggested_data_type',
           'physical_min', 'physical_max', 'typical_min', 'typical_max']

def code_dkg_connection(dkg_targets, gpt_key, ontology_terms=DEFAULT_TERMS, ontology_attribs=DEFAULT_ATTRIBS):

    gromet_fn_module = json_to_gromet("gromet/CHIME_SIR_while_loop--Gromet-FN-auto.json")
    nops = query.collect_named_output_ports(gromet_fn_module)

    terms = list(build_local_ontology(ontology_terms, ontology_attribs).keys())
    variables = set()
    var_dict = {}
    for nop in nops:
        if nop[1] is not None:
            variables.add(nop[0])
            var_dict[nop[0]] = nop

    vlist = []
    for v in list(variables):
        vlist.append((var_dict[v][2].to_dict()['line_begin'], v, var_dict[v][1].to_dict()['value']))
    connection = []
    for t in dkg_targets:
        prompt = get_code_dkg_prompt(vlist, terms, t)
        match = get_gpt_match(prompt, gpt_key)
        val = match.split("(")[1].split(",")[0]

        connection.append((t, {val: "grometSubObject"}, float(var_dict[val][1].to_dict()['value']),
                           var_dict[val][2].to_dict()['line_begin']))

    print(connection)
    return connection

if __name__ == "__main__":
    # code_dkg_connection("population", "") # GPT key
    vars = read_text_from_file('/Users/chunwei/Downloads/example.json')
    dataset = read_text_from_file('../resources/dataset/headers.txt')
    match, _ = vars_dataset_connection(vars, dataset, GPT_KEY)
    print(match)

    # for latex_var in match:
    #     print(latex_var, match[latex_var])
    #     print('\n')