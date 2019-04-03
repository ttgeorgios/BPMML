from lark import Tree, Visitor, Transformer, Lark
import json
import time
import os
import sys, getopt
from colorama import Fore, Style, init

class ReduceTree(Transformer):

    # if a command node is read, we transform the command subtree to a dictionary for later json conversion
    def command(self, args):
        command = ""
        for token in args:
            command += " " + token
        return {"type":"singleCommand", "commands":command.lstrip()}

    # if a user node is read, we transform the user subtree to a dictionary for later json conversion
    def user(self, args):
        div = args[0] #this is the division
        dep = args[1] #this is the department
        pos = args[2] #this is the position
        name = ""
        for token in args[3:]:
            name+= " " + token
        return {"div":div, "dep":dep, "pos":pos, "name":name.lstrip()}


    # if a steps node is read, we transform the steps subtree to a list. Note that we work bottom up so all the sub nodes are already transformed
    def steps(self, args):
        steps = []
        for token in args:
            if str(token) != '\n' and str(token) != "continue": #discarding the line change character
                steps.append(token)
        return steps

    # if a callstep node is read (call command), we check the readyProcessList (which contains all the processes we already transformed) and
    # we transform the node by replacing it with the called process
    def callstep(self, args):
        name = args[1]
        # if the process called in not in the readyProcessList, we print an error (if the bpmml code was correct, this would never happen) 
        if name not in readyProcessDict:
            print(Fore.RED + "Error: " + Fore.RESET + "Process " + name + " does not exist or is defined bellow the call")
            exit()
        return readyProcessDict[name]

    # if a parallelstep node is read, we transform the parallelstep subtree to a dictionary.
    def parallelstep(self, args):
        # we need to check and return the first node that is not a linechange as we allow empty lines
        for data in args[2:-1]:
            if str(data) != '\n':
                for step in data:
                    if step["type"] == "changeUsers": #changing users directly in a parallel block (no process) makes no sense therefore we print an error  
                        print(Fore.RED+ "Error: " + Fore.RESET + "You are changing users directly within a 'parallel' node.")
                        exit()
                return {"type":"parallelSteps", "commands":data}

    # if a yes node is read, we replace it with the already transform children as commands of the yes block (replace it with a dictionary)
    def yes(self, args):
        dataList = []
        for data in args[2:-1]:
            if str(data) != '\n': 
                if str(data) == "abort" or str(data) == "retry": #if the data is abort or retry we can return as those are always the last commands in a yes/no block
                    dataList.append(str(data))
                    return dataList
                for step in data:
                    if step["type"] == "changeUsers": #changing users directly in a yes block (no process) can cause instability so we don't allow it (might change code to allow it later)
                        print(Fore.RED+ "Error: " + Fore.RESET + "You are changing users directly within a 'yes' node. Use a process or change users afterwards")
                        exit()
                dataList = data
        return dataList
    # the exact same code as yes trasformation, will beautify the code on a later date
    def no(self, args):
        dataList = []
        for data in args[2:-1]:
            if str(data) != '\n': 
                if str(data) == "abort" or str(data) == "retry":
                    dataList.append(str(data))
                    return dataList
                for step in data:
                    if step["type"] == "changeUsers":
                        print(Fore.RED+ "Error: " + Fore.RESET + "You are changing users directly within a 'no' node. Use a process or change users afterwards")
                        exit()
                dataList = data
        return dataList

    # if a checkstep node is read, we replace it with the dictionaries of the already transformed yes and no nodes and we also handle the try block 
    def checkstep(self, args):
        dataDict = {"type":"conditionSteps", "condition":""} #initialised dictionary data
        currentBlock = "try" # "pointer" to the current block (iteration follows)
        argsPos = 2 # "pointer" to the current argument (iteration follows)
        answer = "yes" # points to which answer block (yes/no) we are supposed to write data next
        for data in args[2:-1]:
            if str(data) != '\n':

                if str(data) == "check": currentBlock = "check"

                if currentBlock == "try":
                    for step in data:
                        if step["type"] == "changeUsers": #changing users directly in a try block (no process) can cause instability so we don't allow it (might change code to allow it later)
                            print(Fore.RED+ "Error: " + Fore.RESET + "You are changing users directly within a 'try' node. Use a process or change users beforehand")
                            exit() 
                    dataDict["try"] = data
                elif currentBlock == "check":
                    dataDict["condition"] += " " + data
                    if args[argsPos + 1] == '\n':
                        currentBlock = ""
                else:
                    dataDict[answer] = data
                    answer = "no"
            argsPos += 1
        dataDict["condition"] = dataDict["condition"][7:] #deleting some useless chars from the string

        #if both yes and no blocks contain retry/abort then the flow of the graph will be forced to stop, so we do not allow that.
        if (dataDict["yes"] and dataDict["yes"][-1] in ("retry", "abort")) and (dataDict["no"] and dataDict["no"][-1] in ("retry", "abort")):
            print(Fore.RED + "Error: " + Fore.RESET + "Both condition nodes (yes & no) include retry or abort. Graph forcibly stops.")
            exit()
        return dataDict

    # if a userstep node is read, we transform the usersteps subtree to a dictionary. Note that we work bottom up so all the sub nodes are already transformed
    def userstep(self, args):
        users = {"users":[]}
        for token in args[1:-1]:
            if str(token) != '\n':
                users["users"].append(token)
        return users

    # if a change_ userstep node is read, we transform the change_userstep subtree to an appropriate dictionary for later json conversion
    def change_userstep(self, args):
        add = [] #list with users added
        remove = [] #list with users removed
        temp = add #"pointer" to which command is used at the moment initialised to add for no reason    
        for token in args[2:-1]:
            if str(token) != '\n':
                if str(token) == "add":
                    temp = add
                elif str(token) == "remove":
                    temp = remove
                else:
                    temp.append(token)
        return {"type":"changeUsers", "add":add, "remove":remove}
             

    # if a process node is read, we worked our way to the top therefore we can now extract the json (not supporting process calling yet)
    def process(self, args):
        name = str(args[1])
        visible = "True"
        initialUsers = [] #list of the users defined at the start of the process
        users = [] #list of current users as the process is executed
        if name[0] == "_": visible = "False"
        
        # we scan our data to determine the users after every "change user" block
        for data in args[3:-1]:
            if str(data) != '\n':
                if isinstance(data, dict): #this is roundabout way of determining we are in the "user" block data
                    initialUsers = data["users"]
                    users = initialUsers.copy()
                else:
                    for entry in data:
                        if entry["type"] == "changeUsers":
                            for user in entry["add"]:
                                if user in users:
                                    print(Fore.YELLOW + "Warning: " + Fore.RESET + "You are adding a user that is already in the user list. Will not re-add.")
                                else:
                                    users.append(user)
                            for user in entry["remove"]:
                                if user not in users:
                                    print(Fore.YELLOW + "Warning: " + Fore.RESET + "You are removing a user that is not in the user list. Will ignore.")
                                else:
                                    users.remove(user)
                            entry["currentUsers"] = users.copy()  
                        # if there is an invissible process, we need to visualise the change of users at the end of the process (going back to the users in the superprocess)
                        elif entry["type"] == "process":
                            if entry["visible"] == "False":
                                entry["commands"].append({"type":"changeUsers", "add":[], "remove":[], "currentUsers":users.copy()})
                    if visible == "False" and users: print(Fore.BLUE + "Suggestion: " + Fore.RESET + "You are adding users to invisible processes. Consider making them visible for better organisation.")
        return {"type":"process", "name":name, "visible":visible, "users":initialUsers, "commands":data}

# a process that defines the arguments our compiler accepts (the way it works is standard for Python)
def arguments(argv):
    options = {"pretty": False, "visualise": False, "stylise": "", "output": "", "graphname":""}
    try:
        opts,args = getopt.getopt(argv, "hpv:s:o:", ["help", "pretty", "visualise", "stylise", "output"])
    except getopt.GetoptError:
        print("Help List")
        exit()
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print("Help List")
            exit()
        elif opt in ('-p', "--pretty"):
            options["pretty"] = True
        elif opt in ('-v', "--visualise"):
            options["visualise"] = True
            options["graphname"] = arg
        elif opt in ('-s', "--stylise"):
            options["visualise"] = True
            if arg not in ("full", "minimal", "split"):
                print("Help List")
                exit()
            options["stylise"] = arg
        elif opt in ('-o', "--output"):
            if arg[-1] not in ("/", "\\"): #different locales might have a problem here! 
                print(Fore.BLUE + arg + Fore.RED + " is not a valid folder path\n" + Fore.RESET + "(Use '/' or '\\' depending on your OS)")
                exit()
            options["output"] = arg
    return options



startCode = time.time() #starting code timer
init() #initializing colorama lib support (important for Windows, pointless for Linux)
options = arguments(sys.argv[1:-1]) #receiving arguments in the options dictionary
print("Loading Language")
parser = Lark(open("language.lark", "r"), parser="lalr")

print("Reading Code And Constructing Tree")
start = time.time() #starting sub timer for code analysis/tree construction only
infile = sys.argv[-1] #infile is the argument containing our file name/location
if ".bpmml" not in infile:
    print(Fore.RED + "Invalid Input" + Fore.RESET)
    print("Help List")
    exit()
try:
    readFile = open(sys.argv[-1], "r").read()
except FileNotFoundError:
    print(Fore.BLUE + infile + Fore.RED + " does not exist!" + Fore.RESET)
    exit()

tree = parser.parse(readFile) # tree creation

# we iterate the children of the root to save every global process to processDict
processDict = {}
for child in tree.children:
    if child != "start" and child != "end" and child !='\n':
        name = str(child.children[1])
        if name in processDict.keys():
            print(Fore.RED + "Error: " + Fore.RESET +"Two processes have the same name")
            exit()
        processDict[name] = child
if "main" not in processDict.keys():
    print(Fore.RED + "Error: " + Fore.RESET +" Process 'main' not found")
    exit()

end = time.time() # sub timer end
print("Code Analysis Time: %.3f sec" %(end - start))

# logs      
print("Writting to log")
logfile = open("prelog.txt", "w")
logfile.write(str(tree))
logfilePretty = open("prelog_pretty.txt", "w")
logfilePretty.write(tree.pretty())

#we use a transformer that traverses the trees bottom up and reduces the nodes until it reaches the root
print("Reducing Tree")
start = time.time() # sub timer for transformation 
# we transform every tree in the processDict one by one and then place it in the readyProcessDict
readyProcessDict = {}
for name,process in processDict.items():
    reducedTree = ReduceTree().transform(process)
    readyProcessDict[name] = reducedTree
readyProcessDict["main"]["title"] = infile[:-6] # we append the title of the bpmml code file without .bpmml
with open(options["output"] + "data.json", "w") as output:
    if options["pretty"]:
        json.dump(readyProcessDict["main"], output, indent=4)
    else:
        json.dump(readyProcessDict["main"], output)

end = time.time() # end of sub timer
print("Reduction Time (+JSON): %.3f sec" %(end - start))

if (options["visualise"]):
    if options["stylise"] != "":
        os.system("python3 \"Graph Visualisation/visualiser.py\" -n '" + options["graphname"] + "' -s " + options["stylise"])
    else:
        print(options["graphname"])
        os.system("python3 \"Graph Visualisation/visualiser.py\" -n '" + options["graphname"] + "'")

#print("Writting to log")
#logfile = open("log.txt", "w")
#logfile.write(str(reducedTree))
#logfilePretty = open("log_pretty.txt", "w")
#logfilePretty.write(reducedTree.pretty())

endCode = time.time() # end of timer
print(Fore.GREEN + "Code successfully compiled in" + Fore.CYAN + " %.3f sec"  %(endCode - startCode) + Fore.RESET)
