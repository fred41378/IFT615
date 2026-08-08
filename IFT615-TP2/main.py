from parser import facts


# Retourne la liste de toutes les actions possible peut importe s'il sont valide ou non
def all_actions(objects):
    places = [object for object, type in objects.items() if type == "PLACE"]
    rockets = [object for object, type in objects.items() if type == "ROCKET"]
    cargos = [object for object, type in objects.items() if type == "CARGO"]

    actions = []

    # Une action move pour chaque rocket et chaque paire de places (encore là, peut importe si elle sont valide)
    for r in rockets:
        for p1 in places:
            for p2 in places:
                if p1 == p2:
                    continue
                actions.append((
                    f"move({r},{p1},{p2})",
                    frozenset({("has-fuel", r), ("at", r, p1)}),
                    frozenset({("at", r, p2)}),
                    frozenset({("at", r, p1), ("has-fuel", r)}),
                ))

    # load et unload pour chaque combinaison
    for c in cargos:
        for r in rockets:
            for p in places:
                actions.append((
                    f"load({c},{r},{p})",
                    frozenset({("at", r, p), ("at", c, p)}),
                    frozenset({("in", c, r)}),
                    frozenset({("at", c, p)}),
                ))
                actions.append((
                    f"unload({c},{r},{p})",
                    frozenset({("at", r, p), ("in", c, r)}),
                    frozenset({("at", c, p)}),
                    frozenset({("in", c, r)}),
                ))

    return actions


# Les mutex

def mutex_actions(action1, action2, prop_mutex):
    if action1 == action2:
        return False
    _, prec1, add1, del1 = action1
    _, prec2, add2, del2 = action2

    if add1 & del2 or add2 & del1:  # inconsistance : une action defait ce que l'autre fait
        return True
    if prec1 & del2 or prec2 & del1:  # interference : une action a besoin d'un fait qu'une action enlève
        return True
    for p1 in prec1:
        for p2 in prec2:
            if p1 != p2 and frozenset((p1, p2)) in prop_mutex:
                return True  # besoins concurrents : les preconditions sont deja des mutex
    return False


def mutex_props(prec1, prec2, actions, act_mutex):
    achievers1 = [action for action in actions if prec1 in action[2]]
    achievers2 = [action for action in actions if prec2 in action[2]]
    for a1 in achievers1:
        for a2 in achievers2:
            if a1 == a2:
                return False  # la meme action donne les deux faits -> pas mutex
            if frozenset((a1, a2)) not in act_mutex:
                return False  # une combinaison qui marche existe -> pas mutex
    return True



def expand(prop_layer, prop_mutex, all_acts):
    # Construit un nouveau niveau du graphe a partir du niveau de faits

    # On garde les actions dont toutes les preconditions sont deja
    # vraies (sous-ensemble de prop_layer) et qui ne sont pas mutex entre elles
    applicable = [
        action for action in all_acts
        if action[1] <= prop_layer
           and not any(frozenset((p1, p2)) in prop_mutex
                       for p1 in action[1] for p2 in action[1] if p1 != p2)
    ]
    # On ajoute une action persist" par fait deja vrai
    applicable += [(f"persist{p}", frozenset({p}), frozenset({p}), frozenset())
                   for p in prop_layer]

    # Le prochain niveau de faits = tous les effets ajoutes des actions applicables
    next_props = set()
    for a in applicable:
        next_props |= a[2]

    # 4) On calcule quelles actions de ce niveau sont mutex entre elles.
    act_mutex = set()
    for i, a1 in enumerate(applicable):
        for a2 in applicable[i + 1:]:
            if mutex_actions(a1, a2, prop_mutex):
                act_mutex.add(frozenset((a1, a2)))

    # On calcule quels faits du prochain niveau sont mutex entre eux
    next_prop_mutex = set()
    props = list(next_props)
    for i, p1 in enumerate(props):
        for p2 in props[i + 1:]:
            if mutex_props(p1, p2, applicable, act_mutex):
                next_prop_mutex.add(frozenset((p1, p2)))

    return applicable, frozenset(next_props), next_prop_mutex, act_mutex


def goal_reachable(prop_layer, prop_mutex, goal):
    # Il faut que tous les faits du but soient presents
    # et qu'aucune paire de faits du but ne soit mutex
    if not goal <= prop_layer:
        return False
    return not any(frozenset((p1, p2)) in prop_mutex
                   for p1 in goal for p2 in goal if p1 != p2)


def build_achievers_index(act_layer):
    # Associe chaque fait produit à la liste triée des actions qui le produisent
    index = {}
    for a in act_layer:
        for p in a[2]:
            index.setdefault(p, []).append(a)
    for p in index:
        index[p].sort(key=lambda a: (0 if a[0].startswith("persist") else 1, len(a[1])))
    return index


def build_mutex_adjacency(act_mutex):
    # Associe chaque action à l'ensemble des actions avec lesquelles elle est mutex
    adj = {}
    for pair in act_mutex:
        a1, a2 = tuple(pair)
        adj.setdefault(a1, set()).add(a2)
        adj.setdefault(a2, set()).add(a1)
    return adj


def select_action_sets(goals, chosen, achiever_index, mutex_adj):
    if not goals:
        yield list(chosen)
        return

    goal, rest = goals[0], goals[1:]

    achievers = achiever_index.get(goal, [])

    for a in achievers:
        a_mutex = mutex_adj.get(a, ())
        if any(c in a_mutex for c in chosen):
            continue

        next_chosen = chosen if a in chosen else chosen + [a]
        yield from select_action_sets(rest, next_chosen, achiever_index, mutex_adj)

def backtrack_search(act_layers, act_mutexes, prop_layers, goal, level, no_goods,
                      achiever_indexes, mutex_adjacencies):
    if level == 0:
        return [] if goal <= prop_layers[0] else None

    key = (level, frozenset(goal))
    if key in no_goods:
        return None

    achiever_index = achiever_indexes[level - 1]
    mutex_adj = mutex_adjacencies[level - 1]

    # Heuristique : traiter d'abord le fait le plus contraint
    goals_sorted = sorted(goal, key=lambda g: len(achiever_index.get(g, [])))

    for action_set in select_action_sets(goals_sorted, [], achiever_index, mutex_adj):
        preconds = set()
        for a in action_set:
            preconds |= a[1]
        sub_plan = backtrack_search(act_layers, act_mutexes, prop_layers, preconds, level - 1,
                                     no_goods, achiever_indexes, mutex_adjacencies)
        if sub_plan is not None:
            return sub_plan + [list(action_set)]

    no_goods.add(key)
    return None

def resoudre(initial_state, goal, all_act):
    max_levels = 50
    all_proposition = [frozenset(initial_state)]
    propositions_mutexes = [set()]
    action_layer = []
    actions_mutexes = []
    achiever_indexes = []      # nouveau
    mutex_adjacencies = []     # nouveau
    no_goods = set()
    leveled_off_at = None

    for level in range(max_levels):
        if goal_reachable(all_proposition[-1], propositions_mutexes[-1], goal):
            plan = backtrack_search(action_layer, actions_mutexes, all_proposition, goal, level,
                                     no_goods, achiever_indexes, mutex_adjacencies)
            if plan is not None:
                return plan

        leveled_off = (len(all_proposition) >= 2
                       and all_proposition[-1] == all_proposition[-2]
                       and propositions_mutexes[-1] == propositions_mutexes[-2])
        if leveled_off:
            if leveled_off_at is None:
                leveled_off_at = level
            elif level - leveled_off_at >= 3:
                return None

        applicable, next_props, next_prop_mutex, act_mutex = expand(
            all_proposition[-1], propositions_mutexes[-1], all_act)
        action_layer.append(applicable)
        actions_mutexes.append(act_mutex)
        achiever_indexes.append(build_achievers_index(applicable))     # nouveau
        mutex_adjacencies.append(build_mutex_adjacency(act_mutex))     # nouveau
        all_proposition.append(next_props)
        propositions_mutexes.append(next_prop_mutex)

    return None

if __name__ == "__main__":
    initial_state = set(facts.preconds)
    goal = set(facts.effects)
    all_act = all_actions(facts.objects)

    plan = resoudre(initial_state, goal, all_act)

    if plan is None:
        print("Aucun plan trouver")
    else:
        print(f"Plan trouver en {len(plan)} etapes :")
        for step, actions in enumerate(plan, start=1):
            print(f"  etape {step}: {', '.join(a[0] for a in actions)}")