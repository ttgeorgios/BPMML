from lark import Tree,Transformer, Lark
import json
import time
from pathlib import Path, PurePath
from console import Console

class ReduceTree(Transformer):
    def __init__(self, globalArgs, readyProcessDict, importedProcessDict, importedMainDict, console=Console()):
        self.globalArgs = globalArgs
        self.readyProcessDict = readyProcessDict
        self.importedProcessDict = importedProcessDict
        self.importedMainDict = importedMainDict
        self.console = console
        super().__init__()

    def argumentCheck(self, data):
        ampersand = data.find('&')
        if ampersand != -1:
            if data[ampersand:] in self.globalArgs.keys():
                return data[:ampersand] + self.globalArgs[data[ampersand:]]
            else:
                self.console.warning("You are using & without referencing a valid global argument. " + self.console.colorName(data[ampersand:]) + " will be printed as a string.")
        return data

    # if a command node is read, we transform the command subtree to a dictionary for later json conversion
    def command(self, args):
        command = ""
        for token in args:
            token = self.argumentCheck(token)
            command += " " + token
        return {"type":"singleCommand", "commands":command.lstrip()}

    # if a user node is read, we transform the user subtree to a dictionary for later json conversion
    def user(self, args):
        div = args[0] #this is the division
        dep = args[1] #this is the department
        pos = args[2] #this is the position
        name = ""
        for token in args[3:]:
            token = self.argumentCheck(token)
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
        if args[0] == "call":
            name = args[1]
            if len(args) > 2:
                parentName = args[3]
        else:
            name = args[3]
            if len(args) > 2:
                parentName = args[1]

        if len(args) > 2:
            if parentName[-6:] == ".bpmml":
                parentName = parentName[:-6]
            if parentName not in self.importedProcessDict.keys():
                self.console.error("Import " + self.console.colorName(parentName) + " does not exist or was renamed with 'as' command")
            if name not in self.importedProcessDict[parentName].keys():
                self.console.error("Import " + self.console.colorName(parentName) + "does not contain a process named: " + self.console.colorName(name))
            if self.importedProcessDict[parentName][name]["commands"]:
                return self.importedProcessDict[parentName][name]
            else:
                return '\n'
        # if the process called in not in the readyProcessList, we print an error (if the bpmml code was correct, this would never happen) 
        if name not in self.readyProcessDict.keys():
            if name in self.importedMainDict.keys():
                if self.importedMainDict[name]["commands"]:
                    self.importedMainDict[name]["name"] = name
                    return self.importedMainDict[name]
                else:
                    self.console.error("Import " + self.console.colorName(name) + " is not callable as it has no 'main' process")
            self.console.error("Process " + self.console.colorName(name) + " does not exist or is defined bellow the call")
        if not self.readyProcessDict[name]["commands"]:
                return '\n'
        return self.readyProcessDict[name]

    # if a parallelstep node is read, we transform the parallelstep subtree to a dictionary.
    def parallelstep(self, args):
        # we need to check and return the first node that is not a linechange as we allow empty lines
        for data in args[2:-1]:
            if str(data) != '\n':
                for step in data:
                    if step["type"] == "changeUsers": #changing users directly in a parallel block (no process) makes no sense therefore we print an error 
                        self.console.error("You are changing users directly within a 'parallel' node.") 
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
                        self.console.error("You are changing users directly within a 'yes' node. Use a process or change users afterwards")
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
                        self.console.error("You are changing users directly within a 'yes' node. Use a process or change users afterwards")
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
                            self.console.error("You are changing users directly within a 'try' node. Use a process or change users beforehand")
                    dataDict["try"] = data
                elif currentBlock == "check":
                    data = self.argumentCheck(data)
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
            self.console.error("Both condition nodes (yes & no) include retry or abort. Graph forcibly stops.")
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
                                    self.console.warning("You are adding a user that is already in the user list. Will not re-add.")
                                else:
                                    users.append(user)
                            for user in entry["remove"]:
                                if user not in users:
                                    self.console.warning("You are removing a user that is not in the user list. Will ignore.")
                                else:
                                    users.remove(user)
                            entry["currentUsers"] = users.copy()  
                        # if there is an invissible process, we need to visualise the change of users at the end of the process (going back to the users in the superprocess)
                        elif entry["type"] == "process":
                            if entry["visible"] == "False":
                                entry["commands"].append({"type":"changeUsers", "add":[], "remove":[], "currentUsers":users.copy()})
                    if visible == "False" and users: self.console.suggestion("You are adding users to invisible processes. Consider making them visible for better organisation.")
        return {"type":"process", "name":name, "visible":visible, "users":initialUsers, "commands":data}
