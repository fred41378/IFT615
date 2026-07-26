from facts import facts

def load(c, r, p):
    if rocket_is_at_place(r, p) and cargo_is_at_place(c,p):
        put_cargo_in_rocket(c,r)
        remove_cargo_at_place(c,p)
    else:
        print("cannot load")

def unload(c, r, p):
    if rocket_is_at_place(r,p) and cargo_is_in_rocket(c,r):
        add_cargo_at_place(c,p)
        remove_cargo_in_rocket(c,r)
    else:
        print("cannot unload")

def move(r, p1, p2):
    if rocket_has_fuel(r) and rocket_is_at_place(r,p1):
        move_rocket_to_place(r, p1, p2)
        remove_fuel_from_rocket(r)
        remove_rocket_from_place(r,p1)
    else:
        print("cannot move")

def remove_fuel_from_rocket(r):
    facts.remove_fact(("has-fuel",r))

def remove_rocket_from_place(r, p):
    facts.remove_fact(("at", r, p))

def rocket_has_fuel(r):
    return facts.is_true("has-fuel", r)

def move_rocket_to_place(r, p1, p2):
    facts.remove_fact(("at", r, p1))
    facts.add_fact(("at", r, p2))

def remove_cargo_in_rocket(c, r):
    ...

def add_cargo_at_place(c, p):
    ...

def cargo_is_in_rocket(c, r):
    ...

def rocket_is_at_place(r, p):
    ...

def cargo_is_at_place(c, p):
    ...

def remove_cargo_at_place(r, p):
    ...

def put_cargo_in_rocket(r, p):
    ...