"""
Usage:
  Launch the BPMML compiler from terminal.

Help:
  Command Usage:
      bpmml.exe [options] codefile.bpmml
  Options:
        -h, --help:
            Display this message.
        -V, --version:
            Display the curent version of the BPMML compiler.
        -p, --pretty:
            Prettify the output json file with linebreaks, tabs etc.
        -v, --visualise:
            Run the graph visualiser to export a BPMN graph directly.
        -s, --stylise mode:
            Run the graph visualiser to export a BPMN graph directly using a specified mode.
            mode can be "full", "minimal", "split".
        -o, --output dir:
            Choose the output folder (dir) that the json file will be exported to.
    Defaults:
        -The output folder is the folder containing the BPMML codefile.
        -The default style of the visualisation mode is "split".
  
Module Imports:
  import time
  import sys
  (custom module) from console import Console, arguments
  (custom module) from compiler import compileCode
"""
import time
import sys
from console import Console, arguments
from compiler import compileCode, runVisualiser

options = arguments(sys.argv[1:])
codefile = sys.argv[-1]
startCode = time.time() #starting code timer
console = Console(open_for="w")
compileCode(codefile, console=console, output=options["output"], pretty=options["pretty"])
endCode = time.time() # end of timer
console.success(endCode-startCode)
console.closeLog()
if options["visualise"]:
    try:
        runVisualiser(codefile, options["stylise"], options["output"])
    except Exception:
        console.warning("The visualiser executable was not found. Visualisation aborted.")
        sys.exit()
        