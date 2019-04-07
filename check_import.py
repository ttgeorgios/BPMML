
#online cycle detection for imports. Note that the algorithm works because the graph representation after each step is ALWAYS a connected graph
IMPORTS=[]
def detectCycle(parent, child):
    temp = []
    global IMPORTS
    for thread in IMPORTS:
        head = thread[0]
        tail = thread[-1]
        if parent == tail:
            if child == head:
                return True
            temp.append([head, child])
    temp.append([parent, child])
    IMPORTS += temp
    return False
