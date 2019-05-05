class Toolset():
    _CMD_LIST = ("command1", "command2", "command3")
    def __init__(self, root, globalArgs):
        self.ROOT = root
        self.GLOBAL_ARGS = globalArgs
        self.GLOBAL_PROCS = root["globalProcesses"]
        self.MAIN = root["execute"]

    def newCommand(self, command, cmdstring):
        if command not in self._CMD_LIST or not isinstance(cmdstring, str):
            return {}
        return {"type":"singleCommand", "commands":command + " " + cmdstring}

    def isCommand(self, command):
        if isinstance(command, dict):
            if "type" in command.keys():
                if command["type"] == "singleCommand" and isinstance(command["commands"], str):
                    return True
        return False

    def isUser(self, user):
        if isinstance(user, dict):
            if "div" in user.keys() and "dep" in user.keys() and "pos" in user.keys() and "name" in user.keys():
                if isinstance(user["div"], str) and isinstance(user["dep"], str) and isinstance(user["pos"], str) and isinstance(user["name"], str):
                    return True
        return False

    def newProcess(self, name, file="undefined", visible="True", users=[], commands=[]):
        allOk = True
        if visible not in ("True", "False"):
            visible = "True"
            allOk = False
        correctUsers = []
        for user in users:
            if isinstance(user, dict) and self.isUser(user):
                correctUsers.append(user)
            else:
                allOk = False
        correctCommands = []
        for command in commands:
            if self.isCommand(command) or self.isParallel(command) or self.isConditional(command) or self.isChangeUsers(command) or self.isProcess(command):
                correctCommands.append(user)
            else:
                allOk = False
        return {"type":"process", "file":file, "name":name, "visible":visible, "users":correctUsers, "commands":correctCommands}, allOk

    def newUser(self, name, div="General Division", dep="General Department", pos="General Position"):
        if not isinstance(name, str) or not isinstance(div, str) or not isinstance(dep, str) or not isinstance(pos, str):
            return {}
        return {"div":div, "dep":dep, "pos":pos, "name":name}

    def newChangeUsers(self, users=[]):
        allOk = True
        newUsers = []
        for user in users:
            if self.isUser(user):
                newUsers.append(user)
            else:
                allOk = False
        return {"type":"changeUsers", "add":[], "remove":[], "currentUsers":newUsers}, allOk

    def newConditional(self, condition, tryCommands=[], yesCommands=[], noCommands=[]):
        allOk = True
        correctTry = []
        correctYes = []
        correctNo = []
        if not isinstance(condition, str):
            return {}, False
        for command in tryCommands:
            if self.isCommand(command) or self.isConditional(command) or self.isParallel(command) or self.isProcess(command):
                correctTry.append(command)
            else:
                allOk = False
        for command in yesCommands:
            if command in ("retry", "abort"):
                correctYes.append(command)
                break
            elif self.isCommand(command) or self.isConditional(command) or self.isParallel(command) or self.isProcess(command):
                correctYes.append(command)
            else:
                allOk = False
        for command in noCommands:
            if command in ("retry", "abort"):
                correctNo.append(command)
                break
            elif self.isCommand(command) or self.isConditional(command) or self.isParallel(command) or self.isProcess(command):
                correctNo.append(command)
            else:
                allOk = False
        return {"type": "conditionSteps", "condition": condition, "try":correctTry, "yes":correctYes, "no":correctNo}, allOk

    def newParallel(self, commands=[]):
        allOk = True
        correctCommands = []
        for command in commands:
            if self.isCommand(command) or self.isConditional(command) or self.isParallel(command) or self.isProcess(command):
                correctCommands.append(command)
            else:
                allOk = False
        return {"type":"parallelSteps", "commands":correctCommands}, allOk

    def search(self, command, data):
        foundList = []
        pos = 0

        if not isinstance(data, list):
            return [], False

        if not isinstance(command, dict):
            if isinstance(command, str):
                for block in data:
                    if command == block:
                        foundList.append(pos)
                    pos += 1
                return foundList, True
            return [], False
        
        for block in data:
            if not isinstance(block, dict):
                return [], False
            if command.items() <= block.items():
                foundList.append(pos)
            pos += 1
        return foundList, True

    def add(self, command, data, block="commands", pos=""):
        if command in ("abort", "retry"):
            if not self.isConditional(data):
                return False
            if block not in ("yes", "no"):
                return False
            else:
                if data[block][-1] in ("abort", "retry"):
                    return False
                else:
                    data[block].append(command)
                    return True

        if not (self.isChangeUsers(command) or self.isCommand(command) or self.isConditional(command) or self.isParallel(command) or self.isProcess(command) or self.isUser(command)):
            return False

        if self.isConditional(data):
            if block not in ("try", "yes", "no"):
                return False
            elif self.isChangeUsers(command) or self.isUser(command):
                return False
            else:
                if pos == "":
                    data[block].append(command)
                    return True
                else:
                    data[block].insert(pos, command)
                    return True

        if self.isChangeUsers(data):
            if not self.isUser(command):
                return False
            if pos == "":
                data["currentUsers"].append(command)
                return True
            else:
                data["currentUsers"].insert(pos, command)
                return True

        if self.isParallel(data):
            if self.isChangeUsers(command) or self.isUser(command):
                return False
            else:
                if pos == "":
                    data["commands"].append(command)
                    return True
                else:
                    data["commands"].insert(pos, command)
                    return True

        if self.isProcess(data):
            if self.isUser(command):
                return False
            if block != "users":
                block = "commands"
            else:
                if pos == "":
                    data[block].append(command)
                    return True
                else:
                    data[block].insert(pos, command)
                    return True

        return False
            
    def pop(self, item, data, block="commands"):
        blockData = []
        if not isinstance(data, dict):
            return [], False
        else:
            if block not in data.keys():
                return [], False
            blockData = data[blockData]
            if not isinstance(blockData, list):
                return [], False
        
        if isinstance(item, int):
            return [blockData.pop(item)], True
        posList = self.search(item, data)
        popList = []
        for pos in posList:
            popList.append(blockData.pop(pos))
        return popList, True




    def isProcess(self, process):
        if isinstance(process, dict):
            if "type" in process.keys() and "name" in process.keys() and "file" in process.keys() and "visible" in process.keys() and "users" in process.keys() and "commands" in process.keys():
                if process["type"] == "process" and process["visible"] in ("True", "False") and isinstance(process["name"], str) and isinstance(process["file"], str) and isinstance(process["users"], list) and isinstance(process["commands"], list):
                    return True
        return False

    def isParallel(self, parallel):
        if isinstance(parallel, dict):
            if "type" in parallel.keys() and "commands" in parallel.keys():
                if parallel["type"] == "parallelSteps" and isinstance(parallel["commands"], list):
                    return True
        return False

    def isConditional(self, conditional):
        if isinstance(conditional, dict):
            if "type" in conditional.keys() and "condition" in conditional.keys() and "try" in conditional.keys() and "yes" in conditional.keys() and "no" in conditional.keys():
                if conditional["type"] == "conditionSteps" and isinstance(conditional["condition"], str) and isinstance(conditional["try"], list) and isinstance(conditional["yes"], list) and isinstance(conditional["no"], list):
                    return True
        return False

    def isChangeUsers(self, change):
        if isinstance(change, dict):
            if "type" in change.keys() and "add" in change.keys() and "remove" in change.keys() and "currentUsers" in change.keys():
                if change["type"] == "changeUsers" and isinstance(change["add"], list) and isinstance(change["remove"], list) and isinstance(change["currentUsers"], list):
                    return True
        return False