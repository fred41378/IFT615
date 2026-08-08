import os
import sys

INPUT_DIRECTORY_PATH = "inputs"

def read_inputs():
    r_ops = ""
    r_facts = ""
    silent = False

    #On permet de choisir r_ops et r_fact en console ou en ligne de commande
    if len(sys.argv) == 1:
        r_ops = input("Entrez le nom du fichier contenant les operations possibles : ")
        r_facts = input("Entrez le nom du fichier qui contient la mise en situation : ")
    elif len(sys.argv) == 3:
        r_ops = sys.argv[1]
        r_facts = sys.argv[2]
    elif len(sys.argv) == 4:
        r_ops = sys.argv[1]
        r_facts = sys.argv[2]
        silent = sys.argv[3]
    else :
        print("Nombre d'arguments invalide: " + str(len(sys.argv)) + " (Expected 3)")
        return False

    # si n'importe quoi est ecrit dans silent, on doit mettre en mode silent
    if silent :
        silent = True

    # Si le nom des fichiers n'ont pas l'extension, on doit la rajouter
    #   Ca permet de rendre le input plus facile et plus indulgeant
    if not r_ops.endswith(".txt"):
        r_ops += ".txt"

    if not r_facts.endswith(".txt"):
        r_facts += ".txt"

    # On doit rajouter le path des fichiers
    if INPUT_DIRECTORY_PATH != "": # Si le path n'est pas definie, on ne rajoute pas de path
        r_ops = INPUT_DIRECTORY_PATH + "/" + r_ops
        r_facts = INPUT_DIRECTORY_PATH + "/" + r_facts

    # Verifier que les fichiers existent
    if not os.path.isfile(r_ops):
        print(f"Aucun fichier \"{r_ops}\" trouve")
        return False

    if not os.path.isfile(r_facts):
        print(f"Aucun fichier \"{r_facts}\" trouve")
        return False

    # Retourne le path des fichiers des ops et des facts
    return r_ops, r_facts, not silent