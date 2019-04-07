from colorama import Fore, Style, init
from pathlib import Path, PurePath
import sys, getopt

HELP = "Help List"

# a process that defines the arguments our compiler accepts (the way it works is standard for Python)
def arguments(argv):
    options = {"pretty": False, "visualise": False, "stylise": "", "output": ""}
    try:
        opts,args = getopt.getopt(argv, "hpvs:o:", ["help", "pretty", "visualise", "stylise", "output"])
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
        elif opt in ('-s', "--stylise"):
            options["visualise"] = True
            if arg not in ("full", "minimal", "split"):
                print("Help List")
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
        self.consoleLog = open("console.log", open_for)
        self.pre = pre

    def error(self, message="Unidentified error was caught"):
        print(self.pre + Fore.RED + "Error: " + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Error: " + message + '\n')
        exit()

    def warning(self, message="Unidentified warning was caught"):
        print(self.pre + Fore.YELLOW + "Warning:" + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Warning: " + message + '\n')

    def suggestion(self, message="Unidentified suggestion was caught"):
        print(self.pre + Fore.BLUE + "Suggestion: " + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Suggestion: " + message + '\n')

    def colorName(self, name):
        return str(Fore.YELLOW + name + Fore.RESET)

    def invalidArg(self, message="Invalid Argument Given"):
        print(self.pre + Fore.RED + message + Fore.RESET)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + message + '\n')
        print(HELP)
        exit()

    def success(self, sec):
        print(self.pre + Fore.GREEN + "Code successfully compiled in" + Fore.CYAN + " %.3f sec"  %(sec) + Fore.RESET)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Code successfully compiled in" + " %.3f sec"  %(sec) + '\n')

    def closeLog(self):
        self.consoleLog.close()
