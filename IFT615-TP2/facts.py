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

def parse_file(filepath):
    with open(filepath, "r") as f:
        text = f.read()
    splits = prepare(text)
    expressions = []
    while splits:
        expressions.append(parse(splits))
    return expressions

class Facts:
    def __init__(self, filepath):
        self.objects = {}
        self.preconds = []
        self.effects = []
        self._load(filepath)

    def _load(self, filepath):
        expressions = parse_file(filepath)
        for e in expressions:
            if e[0] == "preconds":
                self.preconds = [tuple(fact) for fact in e[1:]]
            elif e[0] == "effects":
                self.effects = [tuple(fact) for fact in e[1:]]
            else:
                self.objects[e[0]] = e[1]

    def add_fact(self, fact):
        self.preconds.append(fact)

    def remove_fact(self, fact):
        if fact in self.preconds:
            self.preconds.remove(fact)

    def is_true(self, fact):
        return fact in self.preconds

    def get_all_facts(self):
        return self.preconds
    def get_all_objects(self):
        return self.objects

facts = Facts("r_fact3.txt")
