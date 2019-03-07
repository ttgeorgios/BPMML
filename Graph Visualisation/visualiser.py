from graphviz import Digraph
import json
import os
os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'

g = Digraph('G', filename='graph')
g.attr(rankdir='LR' )

class Graph:

    def __init__(self, data, startingNode):
        self.counter = 0
        self.startingNode = startingNode
        self.data = data
        self.createGraph(startingNode, data, True)

    def createSimpleNode(self, name, label):
        g.node(name, label, shape="box", style="rounded, filled", fillcolor="yellow2")

    def createParallelNode(self, name, label):
        if label == "":
            g.node(name, label, shape="point")
        else:
            g.node(name, label, shape="diamond", fontsize="12", height="0", width="0", style="filled", fillcolor="orange2")

    def createGraph(self, previousNode, nodeList, isLinear):
        for entry in nodeList:
            self.counter+=1
            name = str(self.counter)
            if entry["type"] == "singleCommand":
                #g.node(name, entry["commands"], shape="box")
                self.createSimpleNode(name, entry["commands"])
                g.edge(previousNode, name)
                previousNode = name
            if entry["type"]  == "parallelSteps":
                #g.node(name, "+", shape="diamond")
                self.createParallelNode(name, "")
                g.edge(previousNode, name)
                self.counter+=1
                name = str(self.counter)
                #g.node(name, "+", shape="diamond")
                self.createParallelNode(name, "+")
                self.createParallel(str(int(name)-1), entry["commands"], name)
                previousNode = name
        g.node("end","", shape="circle", width="0.3", style="filled", fillcolor="red3")
        g.edge(previousNode, "end")

    def createParallel(self, parallelStart, childNodes, parallelEnd):
        for node in childNodes:
            self.counter+=1
            name = str(self.counter)
            if node["type"] == "singleCommand":
                self.createSimpleNode(name, node["commands"])
                g.edge(parallelStart, name)
                g.edge(name, parallelEnd)
            if node["type"]  == "parallelSteps":
                self.createParallelNode(name, "")
                g.edge(parallelStart, name)
                self.counter+=1
                name = str(self.counter)
                self.createParallelNode(name, "+")
                self.createParallel(str(int(name)-1), node["commands"], name)
                g.edge(name, parallelEnd)
                    

with open('data.json') as f:
    data = json.load(f)

g.node('start',"", shape='circle', width="0.3", style="filled", fillcolor="palegreen1")

Graph(data, 'start')

g.view()