from input import read_inputs
import parser

# Tous les facts sont contenus dans cette variables
all_facts = None

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



def select_action_sets(goals, chosen, act_layer, act_mutex):
    # Choisi une action pour chaque fait du goal, sans
    # jamais prendre deux actions mutex ensemble
    if not goals:
        yield list(chosen)
        return

    goal, rest = goals[0], goals[1:]

    achievers = [a for a in act_layer if goal in a[2]]

    achievers.sort(
        key=lambda a: (0 if a[0].startswith("persist") else 1,len(a[1]))
    )

    for a in achievers:
        if any(frozenset((a, c)) in act_mutex for c in chosen):
            continue

        next_chosen = chosen if a in chosen else chosen + [a]
        yield from select_action_sets(rest, next_chosen, act_layer, act_mutex)


def backtrack_search(act_layers, act_mutexes, prop_layers, goal, level, no_goods):
    # Recherche en arriere

    # au niveau 0 le but doit deja etre vrai dans l'etat initial
    if level == 0:
        return [] if goal <= prop_layers[0] else None

    key = (level, frozenset(goal))
    if key in no_goods:
        return None

    act_layer, act_mutex = act_layers[level - 1], act_mutexes[level - 1]
    for action_set in select_action_sets(list(goal), [], act_layer, act_mutex):
        preconds = set()
        for a in action_set:
            preconds |= a[1]
        sub_plan = backtrack_search(act_layers, act_mutexes, prop_layers, preconds, level - 1, no_goods)
        if sub_plan is not None:
            real_actions = [a for a in action_set ]
            return sub_plan + [real_actions]

    no_goods.add(key)
    return None


def resoudre(initial_state, goal, all_act):
    """
    :param initial_state: l'état initial des préconditions de facts
    :param goal: la liste des effects de facts (la but à atteindre)
    :param all_act: toutes les actions possibles à partir des objets de facts
    :return: un plan fini
    """
    max_levels = 50
    all_proposition = [frozenset(initial_state)]  # niveau 0 = etat initial
    propositions_mutexes = [set()]
    action_layer = []
    actions_mutexes = []
    no_goods = set()
    leveled_off_at = None

    for level in range(max_levels):
        # On tente d'extraire un plan seulement si le but semble atteignable.
        if goal_reachable(all_proposition[-1], propositions_mutexes[-1], goal):
            plan = backtrack_search(action_layer, actions_mutexes, all_proposition, goal, level, no_goods)
            if plan is not None:
                return plan

        # Le graphe "se stabilise" quand les faits et leurs mutex ne
        # changent plus d'un niveau a l'autre. Si ca dure 3 niveaux de
        # suite, construire plus de niveaux ne servira a rien : on arrete.
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
        all_proposition.append(next_props)
        propositions_mutexes.append(next_prop_mutex)

    return None


def main():
    res = read_inputs()

    if not res:  # La lecture des inputs a echouee
        print("Erreur de lecture des fichiers: Abort")
        return

    all_facts = parser.Facts(res[1])

    initial_state = set(all_facts.preconds)
    goal = set(all_facts.effects)
    all_act = all_actions(all_facts.objects)

    plan = resoudre(initial_state, goal, all_act)

    if plan is None:
        print("Aucun plan trouver")
    else:
        print(f"Plan trouver en {len(plan)} etapes :")
        for step, actions in enumerate(plan, start=1):
            print(f"  etape {step}: {', '.join(a[0] for a in actions)}")


if __name__ == "__main__":
    main()