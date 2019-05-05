from colorama import Fore, Style, init
from pathlib import Path, PurePath
import sys, getopt

HELP = "Help List"
VERSION = "Current Version"

# a process that defines the arguments our compiler accepts (the way it works is standard for Python)
def arguments(argv):
    options = {"pretty": False, "visualise": False, "stylise": "", "output": ""}
    try:
        opts,args = getopt.getopt(argv, "hpvVs:o:", ["help", "pretty", "visualise", "stylise", "output", "version"])
    except getopt.GetoptError:
        print(HELP)
        exit()
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print(HELP)
            exit()
        elif opt in ("-V", "--version"):
            print(VERSION)
            exit()
        elif opt in ('-p', "--pretty"):
            options["pretty"] = True
        elif opt in ('-v', "--visualise"):
            options["visualise"] = True
        elif opt in ('-s', "--stylise"):
            options["visualise"] = True
            if arg not in ("full", "minimal", "split"):
                print(HELP)
                exit()
            options["stylise"] = arg
        elif opt in ('-o', "--output"):
            if not Path(arg).is_dir() : #different locales might have a problem here! 
                print(Fore.BLUE + arg + Fore.RED + " is not a valid directory\n" + Fore.RESET)
                exit()
            options["output"] = Path(PurePath(arg)).absolute()
    return options

class Console():

    def __init__(self, pre="", open_for="a"):
        init() #initializing colorama lib support (important for Windows, pointless for Linux)
        self.openLog(open_for=open_for)
        self.pre = pre

    def error(self, message="Unidentified error was caught", line="", exitCompiler=True):
        if line:
            line = "(line " + str(line)+ ") "
        print(self.pre + Fore.RED + "Error: " + Fore.MAGENTA + line + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Error: " + line + message + '\n')
        if exitCompiler: exit()

    def warning(self, message="Unidentified warning was caught", line=""):
        if line:
            line = "(line " + str(line)+ ") "
        print(self.pre + Fore.YELLOW + "Warning: " + Fore.MAGENTA + line + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Warning: " + line + message + '\n')

    def suggestion(self, message="Unidentified suggestion was caught", line=""):
        if line:
            line = "(line " + str(line)+ ") "
        print(self.pre + Fore.BLUE + "Suggestion: " + Fore.MAGENTA + line + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Suggestion: " + line + message + '\n')

    def colorName(self, name):
        return str(Fore.YELLOW + name + Fore.RESET)

    def invalidArg(self, message="Invalid Argument Given"):
        print(self.pre + Fore.RED + message + Fore.RESET)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + message + '\n')
        print(HELP)
        exit()

    def unexpected(self, message):
        string, arrow = message.split('\n')
        cleanString = string.lstrip()
        whitespaceCounter = len(string) - len(cleanString)
        print('\t' +self.colorName(cleanString) + '\n\t' + Fore.RED + arrow[whitespaceCounter:] + Fore.RESET)
        self.consoleLog.write('\t' + cleanString + '\n\t' + arrow[whitespaceCounter:] + '\n')

    def success(self, sec):
        print(self.pre + Fore.GREEN + "Code successfully compiled in" + Fore.CYAN + " %.3f sec"  %(sec) + Fore.RESET)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Code successfully compiled in" + " %.3f sec"  %(sec) + '\n')

    def openLog(self, open_for="a"):
        self.consoleLog = open("console.log", open_for)

    def closeLog(self):
        self.consoleLog.close()
