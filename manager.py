from tkinter import Button, Frame, Tk, INSERT, END
from tkinter import scrolledtext
from tkinter import messagebox

window = Tk()
window.title("Manager")
window.resizable(False, False)

txt = scrolledtext.ScrolledText(window,width=40,height=20, font=("Sans", 14))
txt.grid(column=0,row=0, pady=8, padx=8)

buttonArea = Frame()
buttonArea.grid(column=1, row=0, sticky="N", pady=8, padx=8)

def readFile(filename):
    input = open(filename + ".lark", 'r')
    global currentFile
    currentFile = filename
    text = input.read()
    input.close()
    text = text.replace(" | ", '\n')
    text = text.replace('"', '')
    text = text.replace(filename.upper() + ": ", '')
    txt.delete(1.0,END)
    txt.insert(INSERT, text)
    print(text)

def save():
    text = txt.get(1.0, END)
    output = currentFile.upper() + ":"
    itemlist = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            if line in itemlist:
                continue
            itemlist.append(line)
            output += ' "' + line.strip() + '" |'
    out = open(currentFile + ".lark", 'w')
    out.write(output[:-1])
    out.close()
    global saved
    saved = True
    messagebox.showinfo('Saved', 'Save Complete')

saveButton = Button(window, text="Save",state="disabled", width=15, command=save)
saveButton.grid(column=1, row=0, pady=8, padx=2, sticky="S")

saved = True

def divClick():
    global saved
    if not saved:
        answer = messagebox.askyesno("Question","Save Changes?")
        if answer == True:
            save()
    
    readFile("division")
    window.title("Manager - Divisions")
    saved = False
    saveButton.config(state="normal", text="Save Divisions")

divButton = Button(buttonArea, text="Open Divisions", width=15, command=divClick)
divButton.grid(column=1, row=0, pady=4, padx=2)

def depClick():
    global saved
    if not saved:
        answer = messagebox.askyesno("Question","Save Changes?")
        if answer == True:
            save()

    readFile("department")
    window.title("Manager - Departments")
    saved = False
    saveButton.config(state="normal", text="Save Department")

depButton = Button(buttonArea, text="Open Departments", width=15, command=depClick)
depButton.grid(column=1, row=1, pady=4, padx=2)

def posClick():
    global saved
    if not saved:
        answer = messagebox.askyesno("Question","Save Changes?")
        if answer == True:
            save()

    readFile("position")
    window.title("Manager - Positions")
    saved = False
    saveButton.config(state="normal", text="Save Positions")

posButton = Button(buttonArea, text="Open Positions", width=15, command=posClick)
posButton.grid(column=1, row=2, pady=4, padx=2)

def on_closing():
    global saved
    if not saved:
        answer = messagebox.askyesno("Question","Save Changes?")
        if answer == True:
            save()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

window.mainloop()