import re
import json
from subprocess import run
from pathlib import Path, PurePath
from lark import Tree,Transformer,Lark,Token, UnexpectedInput
from console import Console
from transformer import ReduceTree
from check_import import detectCycle
from toolset import Toolset

#startCode = time.time() #starting code timer
#options = arguments(sys.argv[1:-1]) #receiving arguments in the options dictionary
#COMPILER_PATH = str(Path("transformer.py").absolute())
VISUALISER_PATH = str(Path("Graph Visualisation/visualiser.py").absolute())

def loadLanguage(language="language.lark", algorithm="lalr"):
    #print("Loading Language")
    scripts = []
    parser = Lark(open(language, "r"), parser=algorithm, lexer_callbacks={'SCRIPT': scripts.append})
    return parser, scripts

def loadCode(codefile, console=Console()):
    #print("Reading Code And Constructing Tree")
    #infile = sys.argv[-1] #infile is the argument containing our file name/location
    if ".bpmml" not in codefile:
        console.invalidArg("Invalid Input")
    try:
        readFile = open(codefile, "r").read()
    except FileNotFoundError:
        console.error(console.colorName(codefile) + " does not exist!")
    return readFile

def parseCode(parser, readFile, console=Console()):
    try:
        tree = parser.parse(readFile) # tree creation
    except UnexpectedInput as u:
        
        exc_class = u.match_examples(parser.parse, {
            "Missing " + console.colorName("start")  + ":" : ["dummy"],
            "Invalid task/command " + console.colorName(u.get_context(readFile).split()[0]) + ":" : ["start \n process main \n dummy \n end \n end"],
            "Invalid department in user definition:" : ["start \n process main \n users \n div1 dummy \n end \n end \n end"],
            "Invalid position in user definition:" : ["start \n process main \n users \n div1 dep1 dummy \n end \n end \n end"]
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
        exit()
    return tree

# we iterate the children of the root to save every global process to processDict
def handleRootChildren(tree, codefile, output="", console=Console(), globalArgs = {}):
    processDict = {}
    importedProcessDict = {}
    importedMainDict = {}
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
            #print(variableList)
            name = "&" + argumentList[0].strip()
            if name not in globalArgs.keys():
                globalArgs[name] = argumentList[1].strip()
            if appendLineNum: globalArgs["#" + name] = subchild.line

def importstep(children, globalArgs, importedProcessDict, importedMainDict, codefile, output="", console=Console()):
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
        #run(["python3", COMPILER_PATH, "-p", "-o", str(output), importedName])
        console.closeLog() #closing and re-opening to append instead of write
        console.openLog()
        compileCode(importedName, Console(pre=console.pre + "In " + console.colorName(importedName) + ": \n\t"), pretty=True, output=output, importedArgs=importedArgs)
        path = str(output / PurePath(importedName).stem)
    else:
        #run(["python3", COMPILER_PATH, "-p", importedName])
        console.closeLog() #closing and re-opening to append instead of write
        console.openLog()
        compileCode(importedName, Console(pre=console.pre + "In " + console.colorName(importedName) + ": \n\t"), pretty=True, importedArgs=importedArgs)
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


# logs      
# print("Writting to log")
# logfile = open("prelog.txt", "w")
# logfile.write(str(tree))
# logfilePretty = open("prelog_pretty.txt", "w")
# logfilePretty.write(tree.pretty())

#we use a transformer that traverses the trees bottom up and reduces the nodes until it reaches the root
def treeReduction(processDict, fileName, globalArgs, importedProcessDict, importedMainDict, console=Console()):
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
    if output:
        codefile = data["title"] + ".bpmml"
    with open(str(output / PurePath(codefile[:-6] + ".json")), "w") as output:
        if prettify:
            json.dump(data, output, indent=4)
        else:
            json.dump(data, output)

#if (options["visualise"]):
def runVisualiser(codefile, stylise="", output=""):
    if stylise:
        #os.system("python3 \"Graph Visualisation/visualiser.py\" -n '" + options["graphname"] + "' -s " + options["stylise"])
        if output:
            run(["python3", VISUALISER_PATH, "-o", str(output), "-s", stylise, str(PurePath(codefile[:-6] + ".json"))])
        else:
            run(["python3", VISUALISER_PATH, "-s", stylise, str(PurePath(codefile[:-6] + ".json"))])
    else:
        #print(options["graphname"])
        #os.system("python3 \"Graph Visualisation/visualiser.py\" -n '" + options["graphname"] + "'")
        if output:
            run(["python3", VISUALISER_PATH, "-o", str(output), str(PurePath(codefile[:-6] + ".json"))])
        else:
            run(["python3", VISUALISER_PATH, str(PurePath(codefile[:-6] + ".json"))])

#print("Writting to log")
#logfile = open("log.txt", "w")
#logfile.write(str(reducedTree))
#logfilePretty = open("log_pretty.txt", "w")
#logfilePretty.write(reducedTree.pretty())
def compileCode(codefile, console=Console(), output="", pretty=False, visualise=False, stylise="", importedArgs={}):
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
    if visualise:
        runVisualiser(codefile, stylise, output)

if __name__ == "__main__":
    console = Console(open_for="w")
    compileCode("cases.bpmml", console, pretty=True)
    console.success(0)
        
        

