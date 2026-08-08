
def prepare(text):
    return text.replace("(", " ( ").replace(")", " ) ").split()

def parse(splits):
    split = splits.pop(0)
    if split == "(":
        list = []
        while splits[0] != ")":
            list.append(parse(splits))
        splits.pop(0)
        return list
    else:
        return split

def parse_file(filepath, trace = False):
    with open(filepath, "r") as f:
        text = f.read()
        if trace:
            print(text)
    splits = prepare(text)
    expressions = []
    while splits:
        expressions.append(parse(splits))
    return expressions

class Facts:
    def __init__(self, filepath, trace = False):
        self.objects = {}
        self.preconds = []
        self.effects = []
        self._load(filepath, trace)

    def _load(self, filepath, trace = False):

        # Si on a une trace, on doit print le header
        if trace:
            print("/*-------------------------------------------------------------------------------*/")
            print("/* ---------------- Description des conditions initiales et des objectifs -------*/")
            print("/*-------------------------------------------------------------------------------*/")

        expressions = parse_file(filepath, trace)
        for e in expressions:
            if e[0] == "preconds":
                self.preconds = [tuple(fact) for fact in e[1:]]
            elif e[0] == "effects":
                self.effects = [tuple(fact) for fact in e[1:]]
            else:
                self.objects[e[0]] = e[1]


class Operator:
    def __init__(self, name, params, preconds, adds, dels):
        self.name = name
        self.params = params      # list of (varname, type)
        self.preconds = preconds  # list of tuples (predicate, var1, var2, ...)
        self.adds = adds          # list of tuples (positive effects)
        self.dels = dels          # list of tuples (negative effects, predicate only, no 'del' tag)


def load_ops(filepath, trace = False):
    operators = []

    # Si on a une trace, on doit print le header
    if trace:
        print("/*-----------------------------------------------------------------------*/")
        print("/* -------------------------- Description des operateurs ----------------*/")
        print("/*-----------------------------------------------------------------------*/\n")

    expressions = parse_file(filepath, trace)
    for e in expressions:
        if e[0] != "operator" or len(e) != 5:
            print("Invalid operator")
            return False

        # Nom de l'op
        name = e[1]

        # Param d'entrees de l'op
        if e[2][0] != "params":
            print("Invalid operator")
            return False
        params = []
        for p in e[2][1:]:
            params.append(tuple(p))

        # preconds d'entrees de l'op
        if e[3][0] != "preconds":
            print("Invalid operator")
            return False
        preconds = []
        for p in e[3][1:]:
            preconds.append(tuple(p))

        # effects d'entrees de l'op
        if e[4][0] != "effects":
            print("Invalid operator")
            return False
        add = []
        delete = []
        for p in e[4][1:]:
            if p[0] == "del":
                delete.append(tuple(p[1:]))
            else:
                add.append(tuple(p))

        operators.append(Operator(name, params, preconds, add, delete))

    return operators

