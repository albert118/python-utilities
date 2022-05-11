import os

import nbformat
from nbconvert import PythonExporter
from tqdm.auto import tqdm

################################################################################

# Extra debug prints
verbose_mode = False

# extension type to convert from (notebook extension)
ipyExtension = ".ipynb"

# master file list to export (notebooks)
filenames = [
    "ArrearsTenanciesCreator",
    "CleanupAutomationSchedules",
    "CreateScheduledAutomations",
    "GetLoadTestingCustomerData",
    "ResultsReview"
]

# build directory
buildPath = os.path.abspath("NotebookScripts")

################################################################################

def ReadNotebook(notebookFile):
    fullFilename = notebookFile + ipyExtension
    _fn = os.path.abspath(fullFilename)
    
    if verbose_mode:
        print(f"Reading {notebookFile} from absolute path {_fn}.")
    
    with open(_fn) as reader:
        nb = nbformat.read(reader, as_version=4)

    return nb

def Export(notebookJson):
    exporter = PythonExporter()
    # source is a tuple of python source code
    # meta contains metadata
    source, meta = exporter.from_notebook_node(notebookJson)
    return source, meta

def ExportToScript(notebookFile, source):
    exportPath = os.path.join(buildPath, notebookFile + ".py") 
    _fn = os.path.abspath(exportPath)

    if verbose_mode:
        print(f"Exporting {notebookFile} to absolute path {_fn}.")

    with open(_fn, 'w+') as writer:
        writer.writelines(source)


def Runner():
    print("\n== STARTING BUILD ==\n")
    
    for file in tqdm(filenames):
        print(f"\nExporting {file} to script...\n")
        nbJson = ReadNotebook(file)
        source, _ = Export(nbJson)
        ExportToScript(file, source)
    
    print("\n== BUILD COMPLETE ==\n")

    print("\n== RESETTING NOTEBOOK CELL OUTPUTS ==\n")
    if(input("Continue ('n' to return without reset)? ").lower().strip() == 'n'):
        return

    # This is currently far easier to perform as a shell execution
    os.system("jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace *.ipynb")

Runner()
