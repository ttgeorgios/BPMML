"""
Classes:
  Toolset() -- tools to edit BPMML's json output.
"""
class Toolset():
    """ 
    Use pre-made methods to manually edit the BPMML's json output file (using Python 3.x).

    Description:
    Toolset() is implemented in the "run" command of BPMML hence every instance variable is meant to look as a Glabal variable.

    Instance Variables:
      ROOT -- dict containing the whole BPMML output file
      GLOBAL_ARGS -- dict containing the name (key) and value (value) of every BPMML Global Argument
      GLOBAL_PROCS -- list containing the BPMML Global Processes (as dicts)
      MAIN --  dict contaning the "main" Process

    Public Methods:
      __init__(self, root, glabalArgs)
      add(self, command, data, block='commands', pos='')
      isChangeUsers(self, change)
      isCommand(self, command)
      isConditional(self, conditional)
      isParallel(self, parallel)
      isProcess(self, process)
      isUser(self, user)
      newChangeUsers(self, users=[])
      newCommand(self, command, cmdstring)
      newConditional(self, condition, tryCommands=[], yesCommands=[], noCommands=[])
      newParallel(self, commands=[])
      newProcess(self, name, file='undefined', visible='True', users=[], commands=[])
      newUser(self, name, div='General Division', dep='General Department', pos='General Position')
      pop(self, item, data, block='commands')
      search(self, command, data)

    Note:
      Code is still in develpment which could be dropped as manually editting the json file is not recommended.
    """

    _CMD_LIST = ("command1", "command2", "command3")
    def __init__(self, root, globalArgs):
        """Intialise Toolset object""" 
        self.ROOT = root
        self.GLOBAL_ARGS = globalArgs
        self.GLOBAL_PROCS = root["globalProcesses"]
        self.MAIN = root["execute"]

    def isCommand(self, command):
        """
        Check if a dict is a valid "command" element and return True/False depending on the result.

        Arguments:
          command -- dict containing a potential "command" element

        Return:
          True if command argument is a valid "command" element
          False otherwise

        Note:
          TypeErrors of the command argument is automatically handled.
        """
        if isinstance(command, dict):
            if "type" in command.keys():
                if command["type"] == "singleCommand" and isinstance(command["commands"], str):
                    return True
        return False

    def isUser(self, user):
        """
        Check if a dict is a valid "user" element and return True/False depending on the result.

        Arguments:
          user -- dict containing a potential "user" element

        Return:
          True if user argument is a valid "user" element
          False otherwise

        Note:
          TypeErrors of the user argument is automatically handled.
        """
        if isinstance(user, dict):
            if "div" in user.keys() and "dep" in user.keys() and "pos" in user.keys() and "name" in user.keys():
                if isinstance(user["div"], str) and isinstance(user["dep"], str) and isinstance(user["pos"], str) and isinstance(user["name"], str):
                    return True
        return False

    def isProcess(self, process):
        """
        Check if a dict is a valid "process" element and return True/False depending on the result.

        Arguments:
          process -- dict containing a potential "process" element

        Return:
          True if process argument is a valid "process" element
          False otherwise

        Note:
          TypeErrors of the process argument is automatically handled.
        """
        if isinstance(process, dict):
            if "type" in process.keys() and "name" in process.keys() and "file" in process.keys() and "visible" in process.keys() and "users" in process.keys() and "commands" in process.keys():
                if process["type"] == "process" and process["visible"] in ("True", "False") and isinstance(process["name"], str) and isinstance(process["file"], str) and isinstance(process["users"], list) and isinstance(process["commands"], list):
                    return True
        return False

    def isParallel(self, parallel):
        """
        Check if a dict is a valid "parallel" element and return True/False depending on the result.

        Arguments:
          parallel -- dict containing a potential "parallel" element

        Return:
          True if parallel argument is a valid "parallel" element
          False otherwise

        Note:
          TypeErrors of the parallel argument is automatically handled.
        """
        if isinstance(parallel, dict):
            if "type" in parallel.keys() and "commands" in parallel.keys():
                if parallel["type"] == "parallelSteps" and isinstance(parallel["commands"], list):
                    return True
        return False

    def isConditional(self, conditional):
        """
        Check if a dict is a valid "conditional" element and return True/False depending on the result.

        Arguments:
          conditional -- dict containing a potential "conditional" element

        Return:
          True if conditional argument is a valid "conditional" element
          False otherwise

        Note:
          TypeErrors of the conditional argument is automatically handled.
        """
        if isinstance(conditional, dict):
            if "type" in conditional.keys() and "condition" in conditional.keys() and "try" in conditional.keys() and "yes" in conditional.keys() and "no" in conditional.keys():
                if conditional["type"] == "conditionSteps" and isinstance(conditional["condition"], str) and isinstance(conditional["try"], list) and isinstance(conditional["yes"], list) and isinstance(conditional["no"], list):
                    return True
        return False

    def isChangeUsers(self, change):
        """
        Check if a dict is a valid "change users" element and return True/False depending on the result.

        Arguments:
          change -- dict containing a potential "change users" element

        Return:
          True if change argument is a valid "change users" element
          False otherwise

        Note:
          TypeErrors of the change argument is automatically handled.
        """
        if isinstance(change, dict):
            if "type" in change.keys() and "add" in change.keys() and "remove" in change.keys() and "currentUsers" in change.keys():
                if change["type"] == "changeUsers" and isinstance(change["add"], list) and isinstance(change["remove"], list) and isinstance(change["currentUsers"], list):
                    return True
        return False

    def newCommand(self, command, cmdstring):
        """
        Create a new "command" element and return it.

        Arguments:
          command -- string containing the command to be used (must be a valid command)
          cmdstring -- string containing the string that accompanies the command (ex "<command> <cmdstring>")

        Return:
          dict containing the valid structure of a "command" element for BPMML usage
          empty dict if invalid arguments are given

        Note:
           TypeErrors within arguments are automatically handled
        """
        if command not in self._CMD_LIST or not isinstance(cmdstring, str):
            return {}
        return {"type":"singleCommand", "commands":command + " " + cmdstring}

    def newProcess(self, name, file="undefined", visible="True", users=[], commands=[]):
        """
        Create a new "process" element and return it within a turple (see Return for more info).

        Arguments:
          name -- string containing the name of the potential process
          file -- (optional) string containing the name of the BPMML file that will contain the potential process. Defaults to "undefined"
          visible -- (optional) string containg True if the potential process will be visible, False otherwise. Defaults to "True"
          users -- (optional) list containing initial "user" elements for the potential process. Defaults to empty list
          commands -- (optional but integral) list of "command" elements to be part of the potential process (in order). Defaults to empty list

        Return:
          turple containing [0] -> the valid structure of a "process" element for BPMML usage, 
                            [1] -> boolean value indicating if there was no errors while creating the "process" element (no errors is True, False otherwise)

        Note:
          TypeErrors and invalid entries within arguments are automatically handled by discarding them and signaling False to be returned in turple [1].
        """
        allOk = True
        # if visible not in ("True", "False"):
        #     visible = "True"
        #     allOk = False
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
        process = {"type":"process", "file":file, "name":name, "visible":visible, "users":correctUsers, "commands":correctCommands}
        if not self.isProcess(process):
            return {}, False
        return process, allOk

    def newUser(self, name, div="General Division", dep="General Department", pos="General Position"):
        """
        Create a new "user" element and return it.

        Arguments:
          name -- string containing the name of the potential user
          div -- (optional) string containing the division of the potential user. Defaults to "General Division"
          dep -- (optional) string containing the department of the potential user. Defaults to "General Department"
          pos -- (optional) string containing the position of the potential user. Defaults to "General Position"

        Return:
          dict containing the valid structure of a "user" element for BPMML usage
          empty dict if invalid arguments are given
           
        Note:
          TypeErrors within arguments are automatically handled.
          Important to note that div, dep, pos arguments can include ANY string.
        """
        if not isinstance(name, str) or not isinstance(div, str) or not isinstance(dep, str) or not isinstance(pos, str):
            return {}
        return {"div":div, "dep":dep, "pos":pos, "name":name}

    def newChangeUsers(self, users=[]):
        """
        Create a new "change users" element and return it within a turple (see Return for more info).

        Arguments:
          users -- (optional but integral) list containing "user" elements for the potential change users element. Defaults to empty list

        Return:
          turple containing [0] -> the valid structure of a "change users" element for BPMML usage, 
                            [1] -> boolean value indicating if there was no errors while creating the "change users" element (no errors is True, False otherwise)

        Note:
          TypeErrors and invalid entries within arguments are automatically handled by discarding them and signaling False to be returned in turple [1].
        """
        allOk = True
        newUsers = []
        for user in users:
            if self.isUser(user):
                newUsers.append(user)
            else:
                allOk = False
        return {"type":"changeUsers", "add":[], "remove":[], "currentUsers":newUsers}, allOk

    def newConditional(self, condition, tryCommands=[], yesCommands=[], noCommands=[]):
        """
        Create a new "conditional" element and return it within a turple (see Return for more info).

        Arguments:
          condition -- string containing the condition of the potential conditional element
          tryCommands -- (optional) list containing "command" elements to be included in the "try" element of the potential conditional element (in order). Defaults to empty list
          yesCommands -- (optional) list containing "command" elements to be included in the "yes" element of the potential conditional element (in order). Defaults to empty list
          tryCommands -- (optional) list containing "command" elements to be included in the "no" element of the potential conditional element (in order). Defaults to empty list

        Return:
          turple containing [0] -> the valid structure of a "conditional" element for BPMML usage, 
                            [1] -> boolean value indicating if there was no errors while creating the "conditional" element (no errors is True, False otherwise)

        Note:
          TypeErrors and invalid entries within arguments are automatically handled by discarding them and signaling False to be returned in turple [1].
        """
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
        """
        Create a new "parallel" element and return it within a turple (see Returns for more info).

        Arguments:
          commands -- (optional but integral) list of "command" elements to be part of the potential parallel (in order). Defaults to empty list

        Return:
          turple containing [0] -> the valid structure of a "parallel" element for BPMML usage, 
                            [1] -> boolean value indicating if there was no errors while creating the "parallel" element (no errors is True, False otherwise)

        Note:
          TypeErrors and invalid entries within arguments are automatically handled by discarding them and signaling False to be returned in turple [1].
        """
        allOk = True
        correctCommands = []
        for command in commands:
            if self.isCommand(command) or self.isConditional(command) or self.isParallel(command) or self.isProcess(command):
                correctCommands.append(command)
            else:
                allOk = False
        return {"type":"parallelSteps", "commands":correctCommands}, allOk

    def search(self, element, data):
        """
        Search for an element directly within a data list and return a list of all the positions it was found in within a turple (see Return for more info).

        Directly within meaning that elements within elements will not be scanned.

        Arguments:
          element -- valid BPMML element (including string), is the needle 
          data -- target valid BPMML element, is the haystack

        Return:
          turple containing [0] -> list of all the positions within the data argument that the element was found, 
                            [1] -> boolean value indicating if there was no errors searching (no errors is True, False otherwise)

        Note:
          TypeErrors and invalid entries within arguments are automatically handled by and signal False to be returned in turple [1].
        """
        foundList = []
        pos = 0

        if not isinstance(data, list):
            return [], False

        if not isinstance(element, dict):
            if isinstance(element, str):
                for block in data:
                    if element == block:
                        foundList.append(pos)
                    pos += 1
                return foundList, True
            return [], False
        
        for block in data:
            if not isinstance(block, dict):
                return [], False
            if element.items() <= block.items():
                foundList.append(pos)
            pos += 1
        return foundList, True

    def add(self, element, data, block="commands", pos=""):
        """
        Insert an element into another valid element and return the result (boolean).

        Arguments:
          element -- valid BPMML element (including string) to be added
          data -- target valid BPMML element
          block -- (optional) string indicating the target structure/block within the data element (ex "conditional" elements contain "try", "yes", "no" blocks). Defaults to "commands"
          pos -- (optional) integer containing the position that the element will be added in. Defaults to empty

        Return:
          boolean True if the addition was successful, False otherwise

        Exceptions:
          pos argument must be "" (empty) or an integer. Except TypeError.

        Note:
          All other TypeErrors and invalid entries (apart form Exceptions section above) are automatically handled and signal a False return. 
        """
        if element in ("abort", "retry"):
            if not self.isConditional(data):
                return False
            if block not in ("yes", "no"):
                return False
            else:
                if data[block][-1] in ("abort", "retry"):
                    return False
                else:
                    data[block].append(element)
                    return True

        if not (self.isChangeUsers(element) or self.isCommand(element) or self.isConditional(element) or self.isParallel(element) or self.isProcess(element) or self.isUser(element)):
            return False

        if self.isConditional(data):
            if block not in ("try", "yes", "no"):
                return False
            elif self.isChangeUsers(element) or self.isUser(element):
                return False
            else:
                if pos == "":
                    data[block].append(element)
                    return True
                else:
                    data[block].insert(pos, element)
                    return True

        if self.isChangeUsers(data):
            if not self.isUser(element):
                return False
            if pos == "":
                data["currentUsers"].append(element)
                return True
            else:
                data["currentUsers"].insert(pos, element)
                return True

        if self.isParallel(data):
            if self.isChangeUsers(element) or self.isUser(element):
                return False
            else:
                if pos == "":
                    data["commands"].append(element)
                    return True
                else:
                    data["commands"].insert(pos, element)
                    return True

        if self.isProcess(data):
            if self.isUser(element):
                return False
            if block != "users":
                block = "commands"
            else:
                if pos == "":
                    data[block].append(element)
                    return True
                else:
                    data[block].insert(pos, element)
                    return True

        return False
            
    def pop(self, item, data, block="commands"):
        """
        Pop all items from a data list and return it within a turple (see Return for more info).

        Item can be an integer or an BPMML element.
        In case of integer, pop the data[item] (item works as a position).
        In case of element, pop all equal elements within data.
        Tip: If you want to delete a specific number of item elements, do posList = search(element, data) then pop any number of elements in the posList positions.   

        Arguments:
          item -- integer or valid BPMML element (including string) to be poped
          data -- target valid BPMML element
          block -- (optional) string indicating the target structure/block within the data element (ex "conditional" elements contain "try", "yes", "no" blocks). Defaults to "commands"

          Return:
            turple containing [0] -> list of all the positions within the data argument that the command argument was found, 
                              [1] -> boolean value indicating if there was no errors searching (no errors is True, False otherwise)

          Exceptions:
            item argument, while integer, must be within the data lenght. Except IndexError.

          Note:
            TypeErrors and invalid entries (apart form Exceptions section above) are automatically handled and signal a False return.
            
        """
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
        posList = self.search(item, data)[0]
        popList = []
        for pos in posList:
            popList.append(blockData.pop(pos))
        return popList, True
