"""
Imports:
  from colorama import Fore, Style, init
  from pathlib import Path, PurePath
  import sys, getopt

Global Variables:
  VERSION -- string containing info about the current version of the BPMML compiler
  HELP -- string containing the help message/usage of the BPMML compiler

Function:
  arguments(argv) -- handle arguments given to the BPMML compiler

Classes:
  Console() -- handle interactions of the compiler with the output stream
"""
from colorama import Fore, Style, init
from pathlib import Path, PurePath
import sys, getopt

VERSION = "1.0.0 pre-release edition"
HELP = "This is the help page of the BPMML compiler (version " + VERSION + ")\n" + """
    Command Usage:
        bpmml.exe [options] <codefile.bpmml>
    Options:
        -h, --help:
            Display this message.
        -V, --version:
            Display the current version of the BPMML compiler.
        -p, --pretty:
            Prettify the output json file with linebreaks, tabs etc.
        -v, --visualise:
            Run the graph visualiser to export a BPMN graph directly.
        -s, --stylise <mode>:
            Run the graph visualiser to export a BPMN graph directly using a specified <mode>.
            <mode> can be "full", "minimal", "split".
        -o, --output <dir>:
            Choose the output folder (<dir>) that the json file will be exported to.
    Defaults:
        -The output folder is the folder containing the BPMML codefile.
        -The default style of the visualisation mode is "split".
    """

# a process that defines the arguments our compiler accepts (the way it works is standard for Python)
def arguments(argv):
    """
    Check and handle environmental arguments given while executing the BPMML compiler

    Arguments:
      argv -- list of arguments (automatically extracted by calling "sys.argv")
    
    Return:
      A dict containing the options, under which the compiler will run, based on the environmental arguments
      Default options are:
        options = {"pretty": False, "visualise": False, "stylise": "", "output": ""}
    
    Note:
      Invalid environmental arguments are automatically caught and force the compiler to show the "help" message, then exit.
    """
    options = {"pretty": False, "visualise": False, "stylise": "", "output": ""}
    try:
        opts,args = getopt.getopt(argv, "hpvVs:o:", ["help", "pretty", "visualise", "stylise", "output", "version"])
    except getopt.GetoptError:
        if ".bpmml" in argv[-1]:
          arguments(argv[:-1])
        print(HELP)
        sys.exit()
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print(HELP)
            sys.exit()
        elif opt in ("-V", "--version"):
            print(VERSION)
            sys.exit()
        elif opt in ('-p', "--pretty"):
            options["pretty"] = True
        elif opt in ('-v', "--visualise"):
            options["visualise"] = True
        elif opt in ('-s', "--stylise"):
            options["visualise"] = True
            if arg not in ("full", "minimal", "split"):
                print(HELP)
                sys.exit()
            options["stylise"] = arg
        elif opt in ('-o', "--output"):
            if not Path(arg).is_dir() : #different locales might have a problem here! 
                print(Fore.BLUE + arg + Fore.RED + " is not a valid directory\n" + Fore.RESET)
                sys.exit()
            options["output"] = Path(PurePath(arg)).absolute()
    return options

class Console():
    """
    Handle output/messages shown to the users of the BPMML compiler

    Description:
      Console() can handle, print, colour and log outputs such as errors, warnings, suggestions etc.

    Instance Variables:
      pre -- strint containing a prefix to be used before every message (helpfull for tabbing)

    Public Methods:
      __init__(self, pre='', open_for='a')
      closeLog(self)
      colorName(self, name)
      error(self, message='Unidentified error was caught', line='', exitCompiler=True)
      invalidArg(self, message='Invalid Argument Given')
      openLog(self, open_for='a')
      success(self, sec)
      suggestion(self, message='Unidentified suggestion was caught', line='')
      unexpected(self, message)
      warning(self, message='Unidentified warning was caught', line='')
    """

    def __init__(self, logdir=str(Path(PurePath(sys.argv[0])).absolute().parents[0]), pre="", open_for="a"):
        """
        Initialise Console object by initialising the coloring library, setting a prefix and preparing a log file.

        Arguments:
          logdir -- (optional) string containing the directory that the console.log lof file will be exported to. Defaults to the BPMML compiler folder
          pre -- (optional) string containing a prefix to be used before every message (helpfull for tabbing). Defaults to empty string
          open_for -- (optional) string containing the method of opening the log file. Defaults to "a" for append

        Exceptions:
          ValueError for invalid mode given to the open_for argument

        Note:
          The log file is created in the same path as the working path.
        """
        init() #initializing colorama lib support (important for Windows, pointless for Linux)
        self.logdir = logdir
        self.openLog(open_for=open_for)
        self.pre = pre

    def error(self, message="Unidentified error was caught", line="", exitCompiler=True):
        """
        Print an error message.

        Arguments:
          message -- (optional) string containing the error message to be printed. Defaults to "Unidentified error was caught"
          line -- (optional) string or int containing the line to be printed as the line the error occurred. Defaults to empty string
          exitCompiler -- (optional) boolean containing True if the compiler must exit after printing the message, False otherwise. Defaults to True

        Note:
          The log file is updated automatically.
        """
        if line:
            line = "(line " + str(line)+ ") "
        print(self.pre + Fore.RED + "Error: " + Fore.MAGENTA + line + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Error: " + line + message + '\n')
        if exitCompiler: sys.exit()

    def warning(self, message="Unidentified warning was caught", line=""):
        """
        Print a warning message.

        Arguments:
          message -- (optional) string containing the warning message to be printed. Defaults to "Unidentified warning was caught"
          line -- (optional) string or int containing the line to be printed as the line the warning occurred. Defaults to empty string

        Note:
          The log file is updated automatically.
        """
        if line:
            line = "(line " + str(line)+ ") "
        print(self.pre + Fore.YELLOW + "Warning: " + Fore.MAGENTA + line + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Warning: " + line + message + '\n')

    def suggestion(self, message="Unidentified suggestion was caught", line=""):
        """
        Print a suggestion message.

        Arguments:
          message -- (optional) string containing the suggestion message to be printed. Defaults to "Unidentified suggestion was caught"
          line -- (optional) string or int containing the line to be printed as the line the suggestion occurred. Defaults to empty string

        Note:
          The log file is updated automatically.
        """
        if line:
            line = "(line " + str(line)+ ") "
        print(self.pre + Fore.BLUE + "Suggestion: " + Fore.MAGENTA + line + Fore.RESET + message)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Suggestion: " + line + message + '\n')

    def colorName(self, name):
        """
        Color a string yellow, which the default "key name" colour.

        Arguments:
          name -- string containing the string to be colored

        Return:
          The colored string 
        """
        return str(Fore.YELLOW + name + Fore.RESET)

    def invalidArg(self, message="Invalid Argument Given"):
        """
        Print an error message specifically for invalid environmental arguments.

        Arguments:
          message -- (optional) string containing the error message to be printed. Defaults to "Invalid Argument Given"

        Note:
          The log file is updated automatically.
          The "help" messages is printed.
          The compiler exits.
        """
        print(self.pre + Fore.RED + message + Fore.RESET)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + message + '\n')
        print(HELP)
        sys.exit()

    def unexpected(self, message):
        """
        Print a visualisation showing the invalid line and underlining any unexpected characters (used in errors, warnings and suggestions).

        Arguments:
          message -- string containing an extracted error string from the compiler (error.get_context())

        Note:
          The log file is updated automatically.
        """
        string, arrow = message.split('\n')
        cleanString = string.lstrip()
        whitespaceCounter = len(string) - len(cleanString)
        print('\t' +self.colorName(cleanString) + '\n\t' + Fore.RED + arrow[whitespaceCounter:] + Fore.RESET)
        self.consoleLog.write('\t' + cleanString + '\n\t' + arrow[whitespaceCounter:] + '\n')

    def success(self, sec):
        """
        Print a compilation success message.

        Arguments:
          sec -- float containing the seconds of code execution

        Note:
          The log file is updated automatically.
          The seconds have 3 decimal points.
        """
        print(self.pre + Fore.GREEN + "Code successfully compiled in" + Fore.CYAN + " %.3f sec"  %(sec) + Fore.RESET)
        self.consoleLog.write(self.pre.replace(Fore.YELLOW,"").replace(Fore.RESET, "") + "Code successfully compiled in" + " %.3f sec"  %(sec) + '\n')

    def openLog(self, open_for="a"):
        """ Open the log file """
        self.consoleLog = open(self.logdir + "/console.log", open_for)

    def closeLog(self):
        """ Close the log file """
        self.consoleLog.close()
