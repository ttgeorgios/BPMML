from lark import Tree, Visitor, Transformer, Lark
import json

class ReduceTree(Transformer):

    # if a command node is read, we transform the command subtree to a dictionary for later json conversion
    def command(self, args):
        command = ""
        for token in args:
            command += " " + token
        return {"type":"singleCommand", "commands":command}

    # if a steps node is read, we transform the steps subtree to a dictionary. Note that we work bottom up so all the sub nodes are already transformed
    def steps(self, args):
        steps = []
        for token in args:
            if str(token) != '\n': #discarding the line change character
                steps.append(token)
        return steps

    # if a parallelstep node is read, we transform the parallelstep subtree to a dictionary.
    def parallelstep(self, args):
        # we need to check and return the first node that is not a linechange as we allow empty lines
        for data in args[2:-1]:
            if data != '\n':
                return {"type":"parallelSteps", "commands":data}

    # if a process node is read, we worked our way to the top therefore we can now extract the json (not supporting process calling yet)
    def process(self, args):
        with open("data.json", "w") as output:
            for data in args[3:-1]:
                if data != '\n':
                    json.dump(data, output)
                    return 1

print("Loading Language")
parser = Lark(open("language.lark", "r"))

print("Reading Code And Constructing Tree")
tree = parser.parse(open("testing.txt", "r").read())

print("Writting to log")
logfile = open("prelog.txt", "w")
logfile.write(str(tree))
logfilePretty = open("prelog_pretty.txt", "w")
logfilePretty.write(tree.pretty())

print("Reducing Tree")
#we use a transformer that traverses the tree bottom up and reduces the nodes until it reaches the root
reducedTree = ReduceTree().transform(tree)

print("Writting to log")
logfile = open("log.txt", "w")
logfile.write(str(reducedTree))
logfilePretty = open("log_pretty.txt", "w")
logfilePretty.write(reducedTree.pretty())
