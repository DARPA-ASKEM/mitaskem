#!/usr/bin/env python
# coding: utf-8

# In[9]:


import json
import ast

from automates.program_analysis.PyAST2CAST import py_ast_to_cast

from automates.program_analysis.JSON2GroMEt.json2gromet import json_to_gromet

from automates.program_analysis.CAST2GrFN import cast
from automates.program_analysis.CAST2GrFN.model.cast import SourceRef
from automates.program_analysis.CAST2GrFN.ann_cast.cast_to_annotated_cast import CastToAnnotatedCastVisitor

from automates.program_analysis.CAST2GrFN.ann_cast.id_collapse_pass import IdCollapsePass
from automates.program_analysis.CAST2GrFN.ann_cast.container_scope_pass import ContainerScopePass
from automates.program_analysis.CAST2GrFN.ann_cast.variable_version_pass import VariableVersionPass
from automates.program_analysis.CAST2GrFN.ann_cast.grfn_var_creation_pass import GrfnVarCreationPass
from automates.program_analysis.CAST2GrFN.ann_cast.grfn_assignment_pass import GrfnAssignmentPass
from automates.program_analysis.CAST2GrFN.ann_cast.lambda_expression_pass import LambdaExpressionPass
from automates.program_analysis.CAST2GrFN.ann_cast.to_gromet_pass import ToGrometPass

from automates.utils.fold import dictionary_to_gromet_json, del_nulls


PYTHON_SOURCE_FILE = "model/x1.py"
PROGRAM_NAME = PYTHON_SOURCE_FILE.rsplit(".")[0].rsplit("/")[-1]


# In[10]:


def run_python_to_cast( python_source_file):
    """ run_python_to_cast reads in a Python source file and creates a CAST object and returns it.
    
        A script that does this and exports it to JSON exists in
        'automates/scripts/program_analysis/python2cast.py'
    """
    program_name = python_source_file.rsplit(".")[0].rsplit("/")[-1]

    # Create the CAST from Python Source
    convert = py_ast_to_cast.PyASTToCAST(program_name, legacy=False)
    contents = ast.parse(open(python_source_file).read())
    C = convert.visit(contents, {}, {})
    C.source_refs = [SourceRef(program_name, None, None, 1, 1)]

    # Return CAST object
    out_cast = cast.CAST([C], "python")
    return out_cast


# In[11]:


def run_cast_to_gromet_pipeline(cast):
    """ run_cast_to_gromet_pipeline converts a CAST object (generated by run_python_to_cast in this notebook)
        to an AnnotatedCAST (AnnCAST) object. It then runs seven passes over this AnnCAST object to generate
        a GroMEt object which is then returned.
        
        A script that does this and exports to JSON exists in
        'automates/scripts/program_analysis/run_ann_cast_pipeline.py'
        
        The individual AnnCAST passes exist under
        'automates/program_analysis/CAST2GrFN/ann_cast/'
    """
    
    visitor = CastToAnnotatedCastVisitor(cast)
    pipeline_state = visitor.generate_annotated_cast()
    
    IdCollapsePass(pipeline_state)
    ContainerScopePass(pipeline_state)
    VariableVersionPass(pipeline_state)
    GrfnVarCreationPass(pipeline_state)
    GrfnAssignmentPass(pipeline_state)
    LambdaExpressionPass(pipeline_state)
    ToGrometPass(pipeline_state)
    
    gromet_object = pipeline_state.gromet_collection
    
    return gromet_object


# In[12]:

def save_gromet_to_file(gromet_object, path):
    with open(path,"w") as f:
        gromet_collection_dict = gromet_object.to_dict()
        f.write(dictionary_to_gromet_json(del_nulls(gromet_collection_dict)))


def run_pipeline_export_gromet(python_source_file):
    """ Runs the two functions in the previous cells to generate CAST and then generate GroMEt
        It then serializes the GroMEt and exports it as a JSON file.
        
        This uses utilities found in
        'automates/utils/fold.py'
        to serialize the GroMEt
    """

    cast = run_python_to_cast(python_source_file)
    gromet_object = run_cast_to_gromet_pipeline(cast)
    program_name = python_source_file.rsplit(".")[0].rsplit("/")[-1]
    save_gromet_to_file(gromet_object, f"{program_name}--Gromet-FN-auto.json")
    print("Generate gormet file " + f"{program_name}--Gromet-FN-auto.json")

# In[13]:


def import_gromet(program_name):
    """ Reads in a GroMEt JSON file and creates a GroMEt object out of it
        This uses utilities found in 
        'automates/program_analysis/JSON2GroMEt.py'
        to import the GroMEt
    """
    gromet_obj = json_to_gromet(f"{program_name}--Gromet-FN-auto.json")
    return gromet_obj





# run_pipeline_export_gromet()
# imported_gromet_obj = import_gromet()
# print(imported_gromet_obj)


# In[ ]:





# In[ ]:




