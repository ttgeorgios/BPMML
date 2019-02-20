from lark import Tree, Visitor, Lark

commandList = []

class SaveCommands(Visitor):
    def command(self, tree):
        assert tree.data == "command"
        command = ""
        for commandNode in tree.children:
             command = command + " " + commandNode
        commandList.append(command) 
            
print("Loading Language")
parser = Lark(open("language.lark", "r"))
print("Reading Code And Constructing Tree")
tree = parser.parse(open("example.txt", "r").read())
print("Calling Visitor")
SaveCommands().visit(tree)
print("Visit Complete")
print("Command List:", commandList)
