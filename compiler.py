"""
Imports:
  import re
  import json
  from subprocess import run
  from pathlib import Path, PurePath
  from lark import Tree,Transformer,Lark,Token, UnexpectedInput
  from console import Console
  from transformer import ReduceTree
  from check_import import detectCycle
  from toolset import Toolset
  import sys

Global Variables:
  VISUALISER_PATH -- string containing the absolute path of the visualiser script
  
Functions:
  compileCode(codefile, console=Console(), output='', pretty=False, importedArgs={})
  exportJSON(codefile, data, output='', prettify=False)
  handleRootChildren(tree, codefile, output='', console=<Console(), globalArgs={})
  importstep(children, globalArgs, importedProcessDict, importedMainDict, codefile, output='', console=Console())
  loadCode(codefile, console=Console())
  loadLanguage(language='language.lark', algorithm='lalr')
  parseCode(parser, readFile, console=Console())
  runScripts(scripts, globalArgs, data, console=Console())    
  runVisualiser(codefile, stylise='', output='')   
  treeReduction(processDict, fileName, globalArgs, importedProcessDict, importedMainDict, console=Console())
  withstep(children, globalArgs, console=Console(), throwError=True, appendLineNum=False)

Notes:
  Could and probably should use a class instead of many functions, but, using functions is more secure in Python (lack of private variables). Could rework it in the future. 
"""
import re
import json
from subprocess import run
from pathlib import Path, PurePath
from lark import Tree,Transformer,Lark,Token, UnexpectedInput
from console import Console
from transformer import ReduceTree
from check_import import detectCycle
from toolset import Toolset
import sys

VISUALISER_PATH = str(Path(PurePath(sys.argv[0])).absolute().parents[0]) + "/Graph Visualisation/visualiser.py"

def loadLanguage(language="language.lark", algorithm="lalr"):
    """
    Load the language .lark file into the script and return the parser (within a turple) to be used to parse any text.

    Arguments:
      language -- (optional) string containing the name of the Lark language file (with extension). Defaults to "language.lark"
      algorithm -- (optional) string containing the name of the parsing algorithm to be used (early, lalr, cyk, None). Defaults to "lalr"

    Return:
      turple containing [0] -> the parser Lark object to be used for parsing any text,
                        [1] -> BETA: a list that will be filled with BPMML SCRIPT commands (if they exist) after parsing any text 

    Exceptions:
       FileNotFoundError for the language argument if the file does not exist
       TypeError for both arguments if they are not strings
       AssertionError for the algorithm argument if it is not a valid parsing algorithm
       MANY potential errors if the language file is invalid
    """
    #print("Loading Language")
    scripts = []
    parser = Lark(open(language, "r", encoding="utf-8"), parser=algorithm, lexer_callbacks={'SCRIPT': scripts.append})
    return parser, scripts

def loadCode(codefile, console=Console()):
    """
    Load the .bpmml code file into the script and return a string containing its contents.

    Arguments:
      codefile -- string containing the filename of the code file to be imported (IMPORTANT: with extension)
      console -- (optional) Console() object used to print data/info. Defaults to a new Console() instance

    Return:
      string containing the contents of the codefile code file

    Exceptions:
      TypeError for the arguments

    Note:
      FileNotFoundError is caught. Also, console will print an Error if codefile is not a bpmml file (the Error will sys.exit() the script) 
    """
    #print("Reading Code And Constructing Tree")
    if ".bpmml" not in codefile:
        console.invalidArg("Invalid Input")
    try:
        readFile = open(codefile, "r").read()
    except FileNotFoundError:
        console.error(console.colorName(codefile) + " does not exist!")
    return readFile

def parseCode(parser, readFile, console=Console()):
    """
    Parse string and return the exported tree.

    Arguments:
      parser -- parser Lark Object containing the parser
      readfile -- string containing the string to be parsed
      console -- (optional) Console() object used to print data/info. Defaults to a new Console() instance

    Exceptions:
      TypeError for invalid readFile type
      AttributeError for invalid parser type

    Notes:
      UnxepectedInput is automatically caught and handled, meaning the it throws a beautified error (and sys.exit()) if the readFile string has an error based on our BPMML language definition
    """
    try:
        tree = parser.parse(readFile) # tree creation
    except UnexpectedInput as u:
        print(u)
        exc_class = u.match_examples(parser.parse, {
            "Missing " + console.colorName("start")  + ":" : ["dummy"],
            "Invalid task/command " + console.colorName(u.get_context(readFile).split()[0]) + ":" : ["start \n process main \n dummy \n end \n end"],
            "Missing the roles in user definition:" : ["start \n process main \n users \n () \n end \n end \n end"],
            "Missing 2 roles in user definition:" : ["start \n process main \n users \n (dummy) \n end \n end \n end", 
                                                "start \n process main \n users \n (dummy,) \n end \n end \n end"],
            "Missing 1 role in user definition:" : ["start \n process main \n users \n (dummy,dummy) \n end \n end \n end", 
                                                "start \n process main \n users \n (dummy,dummy,) \n end \n end \n end"]
        })

        if not exc_class:
            if type(u).__name__ == "UnexpectedToken":
                exc_class = "Unexpected Keyword used: "
            else:
                exc_class = "Unxpected String used: "

        if str(u.__context__) == "'$END'":
            exc_class = "A block is not closing. Expected one or more " + console.colorName("end")
        
        console.error(exc_class, line=u.line, exitCompiler=False)
        console.unexpected(u.get_context(readFile)[:-1])
        sys.exit()
    return tree

def handleRootChildren(tree, codefile, output="", console=Console(), globalArgs = {}):
    """
    Handle every BPMML command/block that is directly inside the start block and return a turple with all the availiable info.

    Handle every node that is a direct child to the root node of the tree.
    Basically handles the following:
      Saves all the global arguments into a dict
      Saves all the global processes (including "main") into a dict
      Saves all imported processes (excluding "main") into a dict
      Saves all imported "main" processes into a different dict

    Arguments:
      tree -- Lark tree object containing the tree exported from parsing 
      codefile -- string containing the filename of the code file to be imported (IMPORTANT: with extension)
      output -- (optional) pathlib.PosixPath object instance containing the output directory. Defaults to empty path (which makes the output directory the current working directory)
      console -- (optional) Console() object used to print data/info. Defaults to a new Console() instance
      globalArgs -- (optional) (edited in-place) dict containing all of the global arguments during the current compilation. Defaults to empty dict

    Return:
      turple containing [0] -> dict containing all of the global processes of current BPMML code file,
                        [1] -> dict containing all of the global arguments of current and imported BPMML code file. It's an in-place addition to the globalArgs argument given,
                        [2] -> dict containing all of the global processes of the imported BPMML code files excluding "main" processes,
                        [3] -> dict containing all of the "main" processes of the imported BPMML code files
    
    Exceptions:
      MANY exceptions depending on invalid arguments
    
    Notes:
      The process dicts contain the name the process as key and the subtree that includes the process as value (apart from the "main" processes that have the .bpmml file names as keys).
      The global arguments dict has the name of the argument as key and the value as value (with some exceptions if appendLineNum is true in the withstep() function, see withstep()) 
    """
    processDict = {}
    importedProcessDict = {}
    importedMainDict = {}
    # we iterate the children of the root to save every global process to processDict
    for child in tree.children:
        if child != "start" and child != "end" and child !='\n':
            if child.data == "withstep":
                withstep(child.children, globalArgs, console)
            elif child.data == "importstep":
                try:
                    importstep(child.children, globalArgs, importedProcessDict, importedMainDict, codefile, output, console)
                except Exception:
                    console.error("Imported BPMML file exported invalid data. If you are running a script, make sure it is valid.", line=child.children[0].line)     
            else:
                name = str(child.children[1])
                if name in processDict.keys():
                    console.error("Two processes have the same name: " + console.colorName(name))
                processDict[name] = child
    return processDict, globalArgs, importedProcessDict, importedMainDict

def withstep(children, globalArgs, console=Console(), throwError = True, appendLineNum = False):
    """
    Handle global argument definition in the BPMML code file and change current data in-place.

    Usage: Used within handleRootChildren() function. Manually using it is not  (many Exceptions may occur).

    Arguments:
      children -- tree nodes containing the children of the "with" command, therefore containing global arguments
      globalArgs -- (edited in-place) dict containing all of the global arguments during the current compilation
      console -- (optional) Console() object used to print data/info. Defaults to a new Console() instance
      throwError -- (optional) boolean containing True if this function is meant to throw an Error (and sys.exit()), False otherwise. Defaults to True
      appendLineNum -- (optional) boolean containing True if this function is meant to add new key/value items in the globalArgs dict with name = "#" + <name of global arg> and value = <line of code that the gloabl arg was assigned a value>, False otherwise. Defaults to False

    Return:
      None

    Notes:
      use thowError to enable the import of global arguments and not throw any errors before all of the imports are complete.
      use appendLineNum to store the lines of imported global arguments so that you can include said lines in any potential Error/Warning messsages.
      see Notes of handleRootChildren() function for more info on the format of dicts.
    """
    for subchild in children:
        if str(subchild) not in ("with", '\n'):
            argumentList = str(subchild).split("=")
            variableList = re.findall("&\w+", argumentList[1])
            for var in variableList:
                var = var.strip()
                varInGlobalArgs = True
                if var not in globalArgs.keys():
                    varInGlobalArgs = False
                    if throwError: console.error(console.colorName(argumentList[0]) + " was given a non existing variable as value ("+console.colorName(var)+")", line=subchild.line)
                if varInGlobalArgs: argumentList[1] = argumentList[1].replace(var, globalArgs[var]) 
            name = "&" + argumentList[0].strip()
            if name not in globalArgs.keys():
                globalArgs[name] = argumentList[1].strip()
            if appendLineNum: globalArgs["#" + name] = subchild.line

def importstep(children, globalArgs, importedProcessDict, importedMainDict, codefile, output="", console=Console()):
    """
    Handle imports in the BPMML code file and change current data in-place.

    Usage: Used within handleRootChildren() function. Manually using it is not  (many Exceptions may occur).

    Arguments:
      children -- tree nodes containing the children of the "import" command
      globalArgs -- (edited in-place) dict containing all of the global arguments during the current compilation
      importedProcessDict -- (edited in-place) dict containing all of the global processes of the imported BPMML code files excluding "main" processes
      importedMainDict -- (edited in-place) dict containing all of the "main" processes of the imported BPMML code files
      codefile -- string containing the filename of the code file to be imported (IMPORTANT: with extension)
      output -- (optional) pathlib.PosixPath object instance containing the output directory. Defaults to empty path (which makes the output directory the current working directory)
      console -- (optional) Console() object used to print data/info. Defaults to a new Console() instance

    Return:
      None

    Note:
      see Notes of handleRootChildren() function for more info on the format of dicts.
    """
    importedName = str(children[1])
    if importedName[-6:] != ".bpmml":
        importedName += ".bpmml"
    if not Path(importedName).is_file():
        importedName = str(PurePath(codefile).parent / importedName)
        if not Path(importedName).is_file():
            console.error(console.colorName(importedName) + " does not exist", line=children[0].line)
    if(detectCycle(codefile, importedName)):
        console.error(console.colorName(codefile) + " tries to import " + console.colorName(importedName) + " but that creates an import cycle", line=children[0].line)
    importedArgs = {}
    withTree = ""
    for child in children:
        if isinstance(child, Tree):
            withTree = child
    if withTree:
        withstep(withTree.children, importedArgs, console, throwError=False, appendLineNum=True)
        for name, value in importedArgs.items():
            if name[0] == "#": continue
            variableList = re.findall("&\w+", value)
            for var in variableList:
                var = var.strip()
                if var not in globalArgs.keys():
                    console.error(console.colorName(name) + " was given a non existing variable as value ("+console.colorName(var)+")", line=importedArgs["#" + name])
                value = value.replace(var, globalArgs[var])
                importedArgs[name] = value
    if output:
        console.closeLog() #closing and re-opening to append instead of write
        console.openLog()
        compileCode(importedName, Console(pre=console.pre + "In " + console.colorName(importedName) + ": \n\t"), pretty=False, output=output, importedArgs=importedArgs)
        path = str(output / PurePath(importedName).stem)
    else:
        console.closeLog() #closing and re-opening to append instead of write
        console.openLog()
        compileCode(importedName, Console(pre=console.pre + "In " + console.colorName(importedName) + ": \n\t"), pretty=False, importedArgs=importedArgs)
        path = str(PurePath(importedName))[:-6]
    importedFile = json.load(open(path + ".json"))
    name = PurePath(importedName).stem
    if Token("AS", 'as') in children:
        name = str(children[3])
    if name in importedProcessDict.keys():
        console.error(console.colorName(importedName) + " is imported multiple times")
    importedProcessDict[name] = {}
    for process in importedFile["globalProcesses"]:
        importedProcessDict[name].update({process["name"]:process})
    importedMainDict[name] = importedFile["execute"] 

#we use a transformer that traverses the trees bottom up and reduces the nodes until it reaches the root
def treeReduction(processDict, fileName, globalArgs, importedProcessDict, importedMainDict, console=Console()):
    """
    Reduce process trees using the transformer.ReduceTree() custom class to compile every global process and return the compiled processes.

    Arguments:
      processDict -- dict containing all of the global arguments of current and imported BPMML code file
      fileName -- string containing the name of the .bpmml file 
      globalArgs -- dict containing all of the global arguments during the current compilation
      importedProcessDict -- dict containing all of the global processes of the imported BPMML code files excluding "main" processes
      importedMainDict -- dict containing all of the "main" processes of the imported BPMML code files
      console -- (optional) Console() object used to print data/info. Defaults to a new Console() instance

    Return:
      dict containing every compilled global processes (compiled means they are now dicts)
    
    Notes:
      the compiled dicts now have the same key (see handleRootChildren() function) but the values are now other dicts (the compiled version of .bpmml is a dict)
    """
    #print("Reducing Tree")
    readyProcessDict = {} 
    # we transform every tree in the processDict one by one and then place it in the readyProcessDict
    for name,process in processDict.items():
        reducedTree = ReduceTree(fileName, globalArgs, readyProcessDict, importedProcessDict, importedMainDict, console).transform(process)
        if name in readyProcessDict.keys():
            console.error("An import has the same name as a process: " + console.colorName(name))
        readyProcessDict[name] = reducedTree
    return readyProcessDict

def runScripts(scripts, globalArgs, data, console=Console()):
    """
    BETA FOR NOW
    """
    tempGlobalArgs = {}
    for key, value in globalArgs.items():
        if key[0] != "#":
            tempGlobalArgs.update({key:value})
    if scripts:
        for script in scripts:
            code = script[4:].strip()
            codetext = ""
            try:
                codetext = open(code, "r").read()
            except FileNotFoundError:
                console.warning("Script " + console.colorName(code) + " does not exist. Will ignore", line=script.line)
            try:
                exec(codetext,{},{"BPMML":Toolset(data, tempGlobalArgs)})
            except Exception as e:
                console.warning("Script " + console.colorName(code) + " has thrown the following Error: " + console.colorName(str(e)), line=script.line)

def exportJSON(codefile, data, output="", prettify=False):
    """ 
    Export json file by converting the data to json.

    Arguments:
      codefile -- string containing the filename of the code file to be imported (IMPORTANT: with extension)
      data -- json convertable data to be converted and extracted
      output -- (optional) pathlib.PosixPath object instance containing the output directory. Defaults to empty path (which makes the output directory the current working directory)
      prettify -- (optional) boolean containing True if the data will be converted using newlines, spacing and tabs, False otherwise. Defaults to False

    Return:
      None
    """
    if output:
        codefile = data["title"] + ".bpmml"
    with open(str(output / PurePath(codefile[:-6] + ".json")), "w") as output:
        if prettify:
            json.dump(data, output, indent=4)
        else:
            json.dump(data, output)

def runVisualiser(codefile, stylise="", output=""):
    """ Run the visualiser script by giving the appropriate arguments to run with."""
    if stylise:
        if output:
            run(["python3", VISUALISER_PATH, "-o", str(output), "-s", stylise, str(PurePath(codefile[:-6] + ".json"))])
        else:
            run(["python3", VISUALISER_PATH, "-s", stylise, str(PurePath(codefile[:-6] + ".json"))])
    else:
        if output:
            run(["python3", VISUALISER_PATH, "-o", str(output), str(PurePath(codefile[:-6] + ".json"))])
        else:
            run(["python3", VISUALISER_PATH, str(PurePath(codefile[:-6] + ".json"))])

def compileCode(codefile, console=Console(), output="", pretty=False, importedArgs={}):
    """Usage: Use in a separate script to compile a .bpmml. Initialise the arguments using environmental arguments (cmd/terminal), see console.py/launcher.py."""
    parser, scripts = loadLanguage()
    fileName = Path(codefile).stem 
    readFile = loadCode(codefile, console)
    tree = parseCode(parser, readFile, console)
    processDict, globalArgs, importedProcessDict, importedMainDict = handleRootChildren(tree, codefile ,output, console, importedArgs)
    readyProcessDict = treeReduction(processDict, fileName, globalArgs, importedProcessDict, importedMainDict, console)
    mainProcess = readyProcessDict.pop("main", {})
    if mainProcess:
        mainProcess["name"] = fileName
    data = {"title":fileName, "globalProcesses":list(readyProcessDict.values()), "execute":mainProcess}
    runScripts(scripts, globalArgs, data, console)
    exportJSON(codefile, data, output, pretty)