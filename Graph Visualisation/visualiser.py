from graphviz import Digraph
import json
import os
from pathlib import Path, PurePath
import sys, getopt

# CODE IS STILL IN EARLY DEVELOPMENT, NO COMMENTS FOR NOW
# CODE IS MESSY AS FUNCTIONALITY IS THE ONLY CONCERN AT THE MOMENT, FOR DEBBUGING REASONS, AS AN IDE/GRAPHICAL-INTERFACE IS ALSO BEING SEPARATELY DEVELOPED 

VERSION = "Alpha"
HELP = "This is the help page of the BPMML visualiser (version " + VERSION + ")\n" + """
    Command Usage:
        visualiser.exe [options] <outfile.json>
    Options:
        -h, --help:
            Display this message.
        -V, --version:
            Display the current version of the BPMML compiler.
        -s, --style <mode>:
            Run the graph visualiser to export a BPMN graph directly using a specified <mode>.
            <mode> can be "full", "minimal", "split".
        -f, --filetype <filetype>:
          Export the graph in a specific filetype.
          <filetype> can be "png", "pdf".
        -o, --output <dir>:
            Choose the output folder (<dir>) that the json file will be exported to.
    Defaults:
        -The output folder is the folder containing the BPMML codefile.
        -The default style of the visualisation mode is "split".
        -The default filetype of the graph is "png".
    """
def arguments(argv):
    options = {"style":"split", "filetype":'png', "output":""}
    try:
        opts,args = getopt.getopt(argv, "hVs:f:o:", ["help", "style", "filetype", "output", "version"])
    except getopt.GetoptError:
        if ".bpmml" in argv[-1]:
            arguments(argv[:-1])
        print(HELP)
        sys.exit()
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print(HELP)
            sys.exit()
        elif opt == ("-V","--version"):
            print(VERSION)
            sys.exit()
        elif opt in ('-s', "--style"):
            if arg not in ("full", "minimal", "split"):
                print(HELP)
                sys.exit()
            options["style"] = arg
        elif opt in ('-f', "--filetype"):
            if arg not in ("png","pdf"):
                print(HELP)
                sys.exit()
            options["filetype"]:arg
        elif opt in ('-o', "--output"):
            if not Path(arg).is_dir() : #different locales might have a problem here! 
                print(arg + " is not a valid directory\n")
                sys.exit()
            options["output"] = Path(PurePath(arg)).absolute()
    return options



# this is the path of Graphviz in Windows OS, you can change it accordingly 
# linux users should be good from the get-go ( sudo apt-get install graphviz )
os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'

graph = Digraph('G', filename='graph')
graph.attr(rankdir='LR', dpi="300")

class Graph:

    def __init__(self, data, startingNode, options):
        self.style = options["style"]
        self.counter = 0
        self.startingNode = startingNode
        self.data = data
        self.superGraph = graph

        if "execute" in data:
            if not data["execute"]:
                for entry in data["globalProcesses"]:
                    self.counter += 1
                    name = str(self.counter)
                    with graph.subgraph(name='cluster_' + name) as c:
                        c.attr(label=entry["name"])
                        c.node(name, "", shape="none")
                        if "users" in entry.keys() and entry["users"]:
                                name = self.createUsers(name, entry["users"], c)
                        endNode = self.createGraph(name, entry["commands"], c)
                        self.counter += 1
                        name = str(self.counter)
                        c.node(name, "", shape="none")
                        c.edge(endNode, name)
            else:
                Graph(data["execute"], startingNode, options)
        else:
            if data["users"]:
                startingNode = self.createUsers(startingNode, data["users"], graph)
            finalNode = self.createGraph(startingNode, data["commands"], graph)
            graph.node("end","", shape="circle", width="0.3", style="filled", fillcolor="red3")
            graph.edge(finalNode, "end")

    def createSimpleNode(self, name, label, g):
        g.node(name, label, shape="box", style="rounded, filled", fillcolor="yellow2")

    def createParallelNode(self, name, label, g):
        if label == "":
            g.node(name, label, shape="point")
        else:
            g.node(name, label, shape="diamond", fontsize="12", height="0", width="0", style="filled", fillcolor="orange2")

    def createUsers(self, previousNode, users, g):
        userString = ''
        for user in users:
            userString += user["div"] + " " + user["dep"] + " " + user["pos"] + " " + user["name"] + '\n'
        userString = userString.replace("- ", "")
        if userString == '':
            userString = "None "
        self.counter += 1
        name = str(self.counter)
        g.node(name, userString[:-1], shape="cds", margin="0.2", fontsize="10", style="filled", fillcolor="cyan")
        userNode = name
        g.edge(previousNode, userNode, arrowhead="none")
        return userNode

    def createGraph(self, previousNode, nodeList, g):
        for entry in nodeList:
            self.counter+=1
            name = str(self.counter)
            if entry["type"] == "singleCommand":
                #g.node(name, entry["commands"], shape="box")
                self.createSimpleNode(name, entry["commands"], g)
                g.edge(previousNode, name)
                previousNode = name
            elif entry["type"]  == "parallelSteps":
                #g.node(name, "+", shape="diamond")
                self.createParallelNode(name, "", g)
                g.edge(previousNode, name)
                self.counter+=1
                name = str(self.counter)
                #g.node(name, "+", shape="diamond")
                self.createParallelNode(name, "+", g)
                self.createParallel(str(int(name)-1), entry["commands"], name, g)
                previousNode = name
            elif entry["type"] == "conditionSteps":
                g.node(name, shape="point")
                g.edge(previousNode, name)
                self.counter+=1
                name = str(self.counter)
                g.node(name, shape="point")
                self.createCondition(str(int(name)-1), entry["condition"], entry["try"], entry["yes"], entry["no"], name, g)
                previousNode = name
            elif entry["type"] == "process":
                hasUsers = False
                if entry["users"]:
                    hasUsers = True
                if entry["visible"] == "False":
                    if hasUsers:
                        previousNode = self.createUsers(previousNode, entry["users"], g)
                    previousNode = self.createGraph(previousNode, entry["commands"], g)
                elif self.style == "full":
                        g.node(name, shape="point", width="0")
                        g.edge(previousNode, name, arrowhead="none")
                        previousNode = name
                        self.superGraph = g
                        with g.subgraph(name='cluster_' + name) as c:
                            c.attr(label=entry["name"])
                            if hasUsers:
                                previousNode = self.createUsers(previousNode, entry["users"], c)
                            previousNode = self.createGraph(previousNode, entry["commands"], c)
                            self.counter += 1
                            name = str(self.counter)
                            c.node(name, shape="point", width="0")
                            c.edge(previousNode, name, arrowhead="none")
                            previousNode = name
                elif self.style == "minimal":
                    g.node(name, "< " + entry["name"], shape="underline")
                    g.edge(previousNode, name, arrowhead="none")
                    previousNode = name
                    if hasUsers:
                        previousNode = self.createUsers(previousNode, entry["users"], g)
                    previousNode = self.createGraph(previousNode, entry["commands"], g)
                    self.counter += 1
                    name = str(self.counter)
                    g.node(name, "End " + entry["name"] + " >", shape="underline")
                    g.edge(previousNode, name)
                    previousNode = name
                else:
                    g.node(name, "Process\n" + entry["name"], shape = "box3d", style="filled", fillcolor="cadetblue1")
                    g.edge(previousNode, name)
                    previousNode = name
                    self.counter += 1
                    name = str(self.counter)
                    with graph.subgraph(name='cluster_' + name) as c:
                            c.attr(label=entry["name"])
                            c.node(name, "", shape="none")
                            if hasUsers:
                                name = self.createUsers(name, entry["users"], c)
                            endNode = self.createGraph(name, entry["commands"], c)
                            self.counter += 1
                            name = str(self.counter)
                            c.node(name, "", shape="none")
                            c.edge(endNode, name)
            elif entry["type"] == "changeUsers":
                previousNode = self.createUsers(previousNode, entry["currentUsers"], g)
        return previousNode
        #g.node("end","", shape="circle", width="0.3", style="filled", fillcolor="red3")
        #g.edge(previousNode, "end")

    def createParallel(self, parallelStart, childNodes, parallelEnd, g):
        for node in childNodes:
            self.counter+=1
            name = str(self.counter)
            if node["type"] == "singleCommand":
                self.createSimpleNode(name, node["commands"], g)
                g.edge(parallelStart, name)
                g.edge(name, parallelEnd)
            elif node["type"]  == "parallelSteps":
                self.createParallelNode(name, "", g)
                g.edge(parallelStart, name)
                self.counter+=1
                name = str(self.counter)
                self.createParallelNode(name, "+", g)
                self.createParallel(str(int(name)-1), node["commands"], name, g)
                g.edge(name, parallelEnd)
            elif node["type"] == "conditionSteps":
                g.node(name, shape="point")
                g.edge(parallelStart, name)
                self.counter+=1
                name = str(self.counter)
                g.node(name, shape="point")
                self.createCondition(str(int(name)-1), node["condition"], node["try"], node["yes"], node["no"], name, g)
                g.edge(name, parallelEnd)
            elif node["type"] == "process":
                hasUsers = False
                if node["users"]:
                    hasUsers = True
                if node["visible"] == "False":
                    if hasUsers:
                        usersNode = self.createUsers(parallelStart, node["users"], g)
                    else:
                        usersNode = parallelStart
                    processEnd = self.createGraph(usersNode, node["commands"], g)
                    g.edge(processEnd, parallelEnd)
                elif self.style == "full":
                    name = str(self.counter)
                    g.node(name, shape="point", width="0")
                    g.edge(parallelStart, name, arrowhead="none")
                    self.superGraph = g
                    with g.subgraph(name='cluster_' + name) as c:
                        c.attr(label=node["name"])
                        if hasUsers:
                            name = self.createUsers(name, node["users"], c)
                        processEnd = self.createGraph(name, node["commands"], c)
                        self.counter += 1
                        name = str(self.counter)
                        c.node(name, shape="point", width="0")
                        c.edge(processEnd, name, arrowhead="none")
                        self.superGraph.edge(name, parallelEnd)
                elif self.style == "minimal":
                    g.node(name, "< " + node["name"], shape="underline")
                    g.edge(parallelStart, name, arrowhead="none")
                    previousNode = name
                    if hasUsers:
                        previousNode = self.createUsers(previousNode, node["users"], g)
                    previousNode = self.createGraph(previousNode, node["commands"], g)
                    self.counter += 1
                    name = str(self.counter)
                    g.node(name, "End " + node["name"] + " >", shape="underline")
                    g.edge(previousNode, name)
                    g.edge(name, parallelEnd)
                else:
                    g.node(name, "Process\n" + node["name"], shape = "box3d", style="filled", fillcolor="cadetblue1")
                    g.edge(parallelStart, name)
                    g.edge(name, parallelEnd)
                    self.counter += 1
                    name = str(self.counter)
                    with graph.subgraph(name='cluster_' + name) as c:
                            c.attr(label=node["name"])
                            c.node(name, "", shape="none")
                            if hasUsers:
                                name = self.createUsers(name, node["users"], c)
                            endNode = self.createGraph(name, node["commands"], c)
                            self.counter += 1
                            name = str(self.counter)
                            c.node(name, "", shape="none")
                            c.edge(endNode, name)

    def createCondition(self, start, condition, trysteps, yessteps, nosteps, end, g):
            tryend = self.createGraph(start, trysteps, g)
            self.counter += 1
            name = str(self.counter)
            g.node(name, condition, shape="diamond", style="filled", fillcolor="orange2")
            g.edge(tryend, name)

            self.counter += 1
            g.node("yesdot" + str(self.counter), shape="point")
            g.edge(name,"yesdot" + str(self.counter), label="yes")
            if yessteps and yessteps[-1] in ("abort", "retry"):
                yesend = self.createGraph("yesdot" + str(self.counter), yessteps[:-1], g)
                self.counter += 1
                if yessteps[-1] == "abort":
                    g.node("abort" + str(self.counter), "", shape="circle", width="0.2", style="filled", fillcolor="red3")
                    g.edge(yesend, "abort" + str(self.counter))
                elif yessteps[-1] == "retry":
                    g.edge(yesend, start)
            else:
                yesend = self.createGraph("yesdot" + str(self.counter), yessteps, g)
                g.edge(yesend, end)

            self.counter += 1
            g.node("nodot" + str(self.counter), shape="point")
            g.edge(name,"nodot" + str(self.counter), label="no")
            if nosteps and nosteps[-1] in ("abort", "retry"):
                noend = self.createGraph("nodot" + str(self.counter), nosteps[:-1], g)
                self.counter += 1
                if nosteps[-1] == "abort":
                    g.node("abort" + str(self.counter), "", shape="circle", width="0.2", style="filled", fillcolor="red3")
                    g.edge(noend, "abort" + str(self.counter))
                elif nosteps[-1] == "retry":
                    g.edge(noend, start)
            else:
                noend = self.createGraph("nodot" + str(self.counter), nosteps, g)
                g.edge(noend, end)

options = arguments(sys.argv[1:])
infile = sys.argv[-1]
with open(str(options["output"] / PurePath(infile))) as f:
    try:
        data = json.load(f)
    except json.decoder.JSONDecodeError:
        print("Invalid Json file, exiting...")
        sys.exit()

try:
    if data["execute"]:
        graph.node("start","", shape='circle', width="0.3", style="filled", fillcolor="palegreen1")

    Graph(data, "start", options)

    graph.attr(label=data["title"])
except Exception:
    print("An unexpected error has occurred while visualising the data. Please make sure you are using a valid Json file.")
    sys.exit()

if options["output"]:
    infile = Path(infile).stem + ".json"
graph.render(filename=str(Path(options["output"] / PurePath(infile[:-5]))), view=True, format=options["filetype"])
