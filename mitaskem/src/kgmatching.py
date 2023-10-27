import pandas as pd 
import numpy as np
from langchain.retrievers import TFIDFRetriever
from langchain.schema import Document
from pathlib import Path

def make_name_doc(tup):
    (name_str, synonym_string) = tup
    if synonym_string == '':
        syns = []
    else:
        syns = synonym_string.split(';')

    if name_str == '':
        name = []
    else:
        name = [name_str]

    keywords = name + syns    
    doc = ';'.join(keywords)
    return doc

def make_desc_doc(tup):
    (name_doc, name_desc) = tup
    if name_doc != '' and name_desc != '':
        return f'{name_doc}: {name_desc}'
    elif name_doc != '':
        return name_doc
    elif name_desc != '':
        return name_desc
    else:
        return ''

def build_node_retriever(kg_node_tsv_path, limit):
    print(f'building index for epi KG from {kg_node_tsv_path}')
    df = pd.read_csv(kg_node_tsv_path, delimiter='\t')
    df = df.rename({'name:string':'name', 'synonyms:string[]':'synonyms', 'id:ID':'id', 'description:string':'description', 'type:string':'type'}, axis=1)
    df = df.assign(**(df[['name', 'synonyms', 'description']].fillna('')))

    df = df.assign(name_doc = df[['name', 'synonyms']].apply(tuple, axis=1).map(make_name_doc))
    df = df.assign(desc_doc = df[['name_doc', 'description']].apply(tuple, axis=1).map(make_desc_doc))
    cleandf = df[~(df.desc_doc == '')]

    docs = cleandf['desc_doc'].values.tolist()
    metas = cleandf[['name', 'synonyms', 'id', 'description', 'type']].apply(dict, axis=1).values.tolist()
    as_docs = [Document(page_content=doc_search, metadata=meta) for (doc_search, meta) in zip(docs, metas)]
    retriever = TFIDFRetriever.from_documents(as_docs, k=limit)
    print('done building index')
    return retriever

## curl -o epi_2023-07-07_nodes.tsv.gz 
# https://askem-mira.s3.amazonaws.com/dkg/epi/build/2023-07-07/nodes.tsv.gz
## unzip epi_2023-07-07_nodes.tsv
import os
from mitaskem.globals import CACHE_BASE

g_kgpath = CACHE_BASE/'epi_nodes.tsv'
g_retriever_filename = 'epi_nodes_retriever'
_g_retriever = None

def _get_retriever():
    ''' initializes and caches retriever from kg nodes file
        use this instead of the global variable directly
    '''
    global _g_retriever
    if not os.path.exists(g_kgpath):
        raise Exception(f'KG file {g_kgpath} does not exist')


    if _g_retriever is None:
        cache_file = (CACHE_BASE/g_retriever_filename).with_suffix('.joblib')

        if cache_file.exists():
            print('loading retriever from cache')
            _g_retriever = TFIDFRetriever.load_local(str(CACHE_BASE), g_retriever_filename)
        else:
            print('building retriever from scratch')
            ret = build_node_retriever(g_kgpath, limit=4)
            ret.save_local(str(CACHE_BASE), g_retriever_filename)
            _g_retriever = ret

        assert cache_file.exists()


    assert _g_retriever is not None
    return _g_retriever


from typing import List
def local_batch_get_mira_dkg_term(term_list : List[str]) -> List[dict]:
    batch_ans = []
    retriever = _get_retriever()
    for term in term_list:
        docs = retriever.get_relevant_documents(term)
        ansdocs = []
        for doc in docs:
            meta = {}
            meta.update(doc.metadata)
            ansdocs.append(meta)

        batch_ans.append(ansdocs)

    return batch_ans