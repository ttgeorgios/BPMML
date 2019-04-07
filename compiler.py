import time
import re
import json
from subprocess import run
from pathlib import Path, PurePath
from lark import Tree,Transformer,Lark,Token
from console import Console
from transformer import ReduceTree
from check_import import detectCycle

#startCode = time.time() #starting code timer
#options = arguments(sys.argv[1:-1]) #receiving arguments in the options dictionary
#COMPILER_PATH = str(Path("transformer.py").absolute())
#VISUALISER_PATH = str(Path("Graph Visualisation/visualiser.py").absolute())

def loadLanguage(language="language.lark", algorithm="lalr"):
    print("Loading Language")
    parser = Lark(open(language, "r"), parser=algorithm)
    return parser

def loadCode(codefile, console=Console()):
    print("Reading Code And Constructing Tree")
    #infile = sys.argv[-1] #infile is the argument containing our file name/location
    if ".bpmml" not in codefile:
        console.invalidArg("Invalid Input")
    try:
        readFile = open(codefile, "r").read()
    except FileNotFoundError:
        console.error(console.colorName(codefile) + " does not exist!")
    return readFile

def parseCode(parser, readFile):
    tree = parser.parse(readFile) # tree creation
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
                importstep(child.children, globalArgs, importedProcessDict, importedMainDict, codefile, output, console)     
            else:
                name = str(child.children[1])
                if name in processDict.keys():
                    console.error("Two processes have the same name: " + console.colorName(name))
                processDict[name] = child
    return processDict, globalArgs, importedProcessDict, importedMainDict

def withstep(children, globalArgs, console=Console(), throwError = True):
    for subchild in children:
        if str(subchild) not in ("with", '\n'):
            argumentList = str(subchild).split("=")
            variableList = re.findall("&\w+", argumentList[1])
            for var in variableList:
                var = var.strip()
                if var not in globalArgs.keys():
                    if throwError: console.error(console.colorName(argumentList[0]) + " was given a non existing variable as value ("+console.colorName(var)+")")
                argumentList[1] = argumentList[1].replace(var, globalArgs[var]) 
            #print(variableList)
            if ("&" + argumentList[0].strip()) not in globalArgs.keys():
                globalArgs["&" + argumentList[0].strip()] = argumentList[1].strip()

def importstep(children, globalArgs, importedProcessDict, importedMainDict, codefile, output="", console=Console()):
    importedName = str(children[1])
    if importedName[-6:] != ".bpmml":
        importedName += ".bpmml"
    if not Path(importedName).is_file():
        importedName = str(PurePath(codefile).parent / importedName)
        if not Path(importedName).is_file():
            console.error(console.colorName(importedName) + " does not exist")
    if(detectCycle(codefile, importedName)):
        console.error(console.colorName(codefile) + " tries to import " + console.colorName(importedName) + " but that creates an import cycle")
    importedArgs = {}
    withTree = ""
    for child in children:
        if isinstance(child, Tree):
            withTree = child
    if withTree:
        withstep(withTree.children, importedArgs, console, throwError=False)
        for name, value in importedArgs.items():
            variableList = re.findall("&\w+", value)
            for var in variableList:
                var = var.strip()
                if var not in globalArgs.keys():
                    console.error(console.colorName(name) + " was given a non existing variable as value ("+console.colorName(var)+")")
                value = value.replace(var, globalArgs[var])
                importedArgs[name] = value
    if output:
        #run(["python3", COMPILER_PATH, "-p", "-o", str(output), importedName])
        compileCode(importedName, Console(pre=console.pre + "In " + console.colorName(importedName) + ": \n\t"), pretty=True, output=output, importedArgs=importedArgs)
        path = str(output / PurePath(importedName).stem)
    else:
        #run(["python3", COMPILER_PATH, "-p", importedName])
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
    print("Reducing Tree")
    readyProcessDict = {} 
    # we transform every tree in the processDict one by one and then place it in the readyProcessDict
    for name,process in processDict.items():
        reducedTree = ReduceTree( globalArgs, readyProcessDict, importedProcessDict, importedMainDict, console).transform(process)
        if name in readyProcessDict.keys():
            console.error("An import has the same name as a process: " + console.colorName(name))
        readyProcessDict[name] = reducedTree
    return readyProcessDict

def exportJSON(codefile, fileName, readyProcessDict, mainProcess, output="", prettify=False):
    data = {"title":fileName, "globalProcesses":list(readyProcessDict.values()), "execute":mainProcess}
    if output:
        codefile = fileName + ".bpmml"
    with open(str(output / PurePath(codefile[:-6] + ".json")), "w") as output:
        if prettify:
            json.dump(data, output, indent=4)
        else:
            json.dump(data, output)

#if (options["visualise"]):
def visualise():
    if options["stylise"] != "":
        #os.system("python3 \"Graph Visualisation/visualiser.py\" -n '" + options["graphname"] + "' -s " + options["stylise"])
        if options["output"]:
            run(["python3", visualiserPath, "-o", str(options["output"]), "-s", options["stylise"], str(PurePath(infile[:-6] + ".json"))])
        else:
            run(["python3", visualiserPath, "-s", options["stylise"], str(PurePath(infile[:-6] + ".json"))])
    else:
        #print(options["graphname"])
        #os.system("python3 \"Graph Visualisation/visualiser.py\" -n '" + options["graphname"] + "'")
        if options["output"]:
            run(["python3", visualiserPath, "-o", str(options["output"]), str(PurePath(infile[:-6] + ".json"))])
        else:
            run(["python3", visualiserPath, str(PurePath(infile[:-6] + ".json"))])

#print("Writting to log")
#logfile = open("log.txt", "w")
#logfile.write(str(reducedTree))
#logfilePretty = open("log_pretty.txt", "w")
#logfilePretty.write(reducedTree.pretty())
def compileCode(codefile, console=Console(), output="", pretty=False, importedArgs={}):
    parser = loadLanguage()
    fileName = Path(codefile).stem 
    readFile = loadCode(codefile, console)
    tree = parseCode(parser, readFile)
    processDict, globalArgs, importedProcessDict, importedMainDict = handleRootChildren(tree, codefile ,output, console, importedArgs)
    readyProcessDict = treeReduction(processDict, fileName, globalArgs, importedProcessDict, importedMainDict, console)
    mainProcess = readyProcessDict.pop("main", {})
    if mainProcess:
        mainProcess["name"] = fileName
    exportJSON(codefile, fileName, readyProcessDict, mainProcess, output, pretty)

if __name__ == "__main__":
    compileCode("with.bpmml", Console(open_for="w"), pretty=True)
        
        

