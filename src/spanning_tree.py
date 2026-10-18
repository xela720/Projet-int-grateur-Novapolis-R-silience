"""Module 4 : Conception du réseau de fibre optique (Arbres couvrants minimaux et résilience).

Implémente :
- Structure Union-Find avec compression de chemin et union par rang.
- Algorithme de Kruskal : O(|E| log |E|).
- Algorithme de Prim avec tas binaire (heapq) : O(|E| log |V|).
- Prise en charge des graphes non connexes (forêt couvrante minimale) et détection des composantes orphelines.
- Gestion des coûts égaux et explication de la multiplicité des arbres minimaux.
- Simulation de panne d'un tronçon de l'arbre et calcul du raccordement de secours au coût minimal dans le graphe initial.
"""

import os
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

import heapq
from collections import deque
from typing import Dict, List, Tuple, Set, Optional, Any

from src.data_manager import GrapheFibre, FibreArete


class UnionFind:
    """Structure de données pour ensembles disjoints avec compression de chemin et rang."""

    def __init__(self, elements: List[str]):
        self.parent: Dict[str, str] = {x: x for x in elements}
        self.rang: Dict[str, int] = {x: 0 for x in elements}
        self.nb_ensembles: int = len(elements)

    def find(self, x: str) -> str:
        """Trouve le représentant de l'élément avec compression de chemin."""
        chemin = []
        courant = x
        while self.parent[courant] != courant:
            chemin.append(courant)
            courant = self.parent[courant]
        for noeud in chemin:
            self.parent[noeud] = courant
        return courant

    def union(self, x: str, y: str) -> bool:
        """Unit les ensembles contenant x et y par rang. Renvoie True si une fusion a eu lieu."""
        racine_x = self.find(x)
        racine_y = self.find(y)

        if racine_x == racine_y:
            return False

        if self.rang[racine_x] < self.rang[racine_y]:
            self.parent[racine_x] = racine_y
        elif self.rang[racine_x] > self.rang[racine_y]:
            self.parent[racine_y] = racine_x
        else:
            self.parent[racine_y] = racine_x
            self.rang[racine_x] += 1

        self.nb_ensembles -= 1
        return True


def kruskal(graphe: GrapheFibre) -> Dict[str, Any]:
    """Calcule l'Arbre Couvrant Minimal (ou Forêt Couvrante) via l'algorithme de Kruskal.

    Complexité : O(|E| log |E|)
    """
    sommets = graphe.sommets()
    uf = UnionFind(sommets)

    aretes_actives = graphe.toutes_les_aretes(uniquement_actifs=True)
    # Tri des arêtes par coût croissant
    aretes_triees = sorted(aretes_actives, key=lambda a: (a.cost, a.extremites()))

    arbre_aretes: List[FibreArete] = []
    cout_total = 0.0

    for arete in aretes_triees:
        if uf.union(arete.u, arete.v):
            arbre_aretes.append(arete)
            cout_total += arete.cost

    # Regroupement des sommets par composante finale
    groupes: Dict[str, Set[str]] = {}
    for s in sommets:
        rep = uf.find(s)
        groupes.setdefault(rep, set()).add(s)

    composantes = sorted(list(groupes.values()), key=len, reverse=True)
    composantes_non_raccordees = composantes[1:] if len(composantes) > 1 else []

    return {
        "aretes": arbre_aretes,
        "cout_total": round(cout_total, 2),
        "est_foret": len(composantes) > 1,
        "nb_composantes": len(composantes),
        "composantes": composantes,
        "composantes_non_raccordees": composantes_non_raccordees,
    }


def prim(graphe: GrapheFibre, sommet_depart: Optional[str] = None) -> Dict[str, Any]:
    """Calcule l'Arbre Couvrant Minimal (ou Forêt Couvrante) via l'algorithme de Prim avec tas binaire.

    Prend en charge les graphes déconnectés en explorant successivement chaque composante.
    Complexité : O(|E| log |V|)
    """
    sommets = graphe.sommets()
    visites: Set[str] = set()
    arbre_aretes: List[FibreArete] = []
    cout_total = 0.0
    composantes: List[Set[str]] = []

    # Ordonnancement des sommets de départ
    file_attente = [sommet_depart] if (sommet_depart and sommet_depart in sommets) else []
    for s in sommets:
        if s not in file_attente:
            file_attente.append(s)

    for depart in file_attente:
        if depart in visites:
            continue

        composante_courante: Set[str] = set()
        visites.add(depart)
        composante_courante.add(depart)

        tas: List[Tuple[float, str, str, FibreArete]] = []
        for v, arete in graphe.voisins(depart, uniquement_actifs=True).items():
            heapq.heappush(tas, (arete.cost, depart, v, arete))

        while tas:
            cout, u, v, arete = heapq.heappop(tas)
            if v in visites:
                continue

            visites.add(v)
            composante_courante.add(v)
            arbre_aretes.append(arete)
            cout_total += cout

            for w, next_arete in graphe.voisins(v, uniquement_actifs=True).items():
                if w not in visites:
                    heapq.heappush(tas, (next_arete.cost, v, w, next_arete))

        composantes.append(composante_courante)

    composantes.sort(key=len, reverse=True)
    composantes_non_raccordees = composantes[1:] if len(composantes) > 1 else []

    return {
        "aretes": arbre_aretes,
        "cout_total": round(cout_total, 2),
        "est_foret": len(composantes) > 1,
        "nb_composantes": len(composantes),
        "composantes": composantes,
        "composantes_non_raccordees": composantes_non_raccordees,
    }


def comparer_kruskal_prim(graphe: GrapheFibre) -> Dict[str, Any]:
    """Compare rigoureusement les arbres couvrants minimaux obtenus par Kruskal et Prim."""
    res_kruskal = kruskal(graphe)
    res_prim = prim(graphe)

    cout_kruskal = res_kruskal["cout_total"]
    cout_prim = res_prim["cout_total"]
    couts_egaux = abs(cout_kruskal - cout_prim) < 1e-4

    set_kruskal = {a.extremites() for a in res_kruskal["aretes"]}
    set_prim = {a.extremites() for a in res_prim["aretes"]}
    aretes_identiques = set_kruskal == set_prim

    explication_multiplicite = ""
    if couts_egaux and not aretes_identiques:
        explication_multiplicite = (
            "Les coûts totaux sont rigoureusement identiques, mais les arêtes sélectionnées diffèrent. "
            "Cela se produit en présence d'arêtes de coûts égaux offrant des chemins alternatifs de même poids."
        )

    return {
        "cout_kruskal": cout_kruskal,
        "cout_prim": cout_prim,
        "couts_egaux": couts_egaux,
        "aretes_identiques": aretes_identiques,
        "nb_aretes_kruskal": len(res_kruskal["aretes"]),
        "nb_aretes_prim": len(res_prim["aretes"]),
        "explication_multiplicite": explication_multiplicite,
    }


def simuler_panne_troncon(
    graphe_initial: GrapheFibre,
    arbre_initial: List[FibreArete],
    arete_en_panne: Tuple[str, str],
) -> Dict[str, Any]:
    """Simule la rupture d'un câble de fibre optique de l'arbre couvrant minimal.

    Méthode :
    1. Retire l'arête rompue de l'arbre.
    2. La rupture scinde la composante de l'arbre en deux sous-arbres C1 et C2.
    3. Recherche dans le graphe initial l'arête active candidate (u in C1, v in C2) au coût minimal.
    4. Reconstruit l'arbre réparé et calcule le surcoût de résilience.
    """
    paire_panne = tuple(sorted(arete_en_panne))

    # Vérification que l'arête faisait bien partie de l'arbre
    arret_retiree = None
    arbres_restant = []
    for a in arbre_initial:
        if a.extremites() == paire_panne:
            arret_retiree = a
        else:
            arbres_restant.append(a)

    if arret_retiree is None:
        raise ValueError(f"L'arête {paire_panne} n'est pas présente dans l'arbre fourni.")

    # Reconstruction de l'adjacence du sous-arbre restant pour trouver C1 et C2
    adj_arbre: Dict[str, List[str]] = {}
    sommets_arbre: Set[str] = set()
    for a in arbres_restant:
        adj_arbre.setdefault(a.u, []).append(a.v)
        adj_arbre.setdefault(a.v, []).append(a.u)
        sommets_arbre.add(a.u)
        sommets_arbre.add(a.v)

    # u_panne et v_panne doivent appartenir aux deux sous-arbres séparés
    u_panne, v_panne = paire_panne
    c1: Set[str] = set()
    file = deque([u_panne])
    c1.add(u_panne)

    while file:
        curr = file.popleft()
        for voisin in adj_arbre.get(curr, []):
            if voisin not in c1:
                c1.add(voisin)
                file.append(voisin)

    c2: Set[str] = set()
    file = deque([v_panne])
    c2.add(v_panne)

    while file:
        curr = file.popleft()
        for voisin in adj_arbre.get(curr, []):
            if voisin not in c2:
                c2.add(voisin)
                file.append(voisin)

    # Recherche de l'arête de secours au coût minimal dans le graphe initial
    meilleure_arete: Optional[FibreArete] = None
    meilleur_cout = float("inf")

    for arete in graphe_initial.toutes_les_aretes(uniquement_actifs=True):
        if arete.extremites() == paire_panne:
            continue  # Ne pas réutiliser le tronçon rompu

        u_dans_c1 = arete.u in c1
        v_dans_c1 = arete.v in c1
        u_dans_c2 = arete.u in c2
        v_dans_c2 = arete.v in c2

        # L'arête doit relier C1 et C2
        if (u_dans_c1 and v_dans_c2) or (u_dans_c2 and v_dans_c1):
            if arete.cost < meilleur_cout:
                meilleur_cout = arete.cost
                meilleure_arete = arete

    if meilleure_arete is not None:
        nouvel_arbre = arbres_restant + [meilleure_arete]
        cout_nouveau = sum(a.cost for a in nouvel_arbre)
        surcout = meilleure_arete.cost - arret_retiree.cost
        succes = True
    else:
        nouvel_arbre = arbres_restant
        cout_nouveau = sum(a.cost for a in nouvel_arbre)
        surcout = float("inf")
        succes = False

    return {
        "succes_reparation": succes,
        "arete_en_panne": paire_panne,
        "cout_arete_initiale": arret_retiree.cost,
        "arete_remplacement": meilleure_arete.extremites() if meilleure_arete else None,
        "cout_remplacement": meilleure_arete.cost if meilleure_arete else None,
        "surcout": round(surcout, 2) if surcout != float("inf") else None,
        "cout_total_nouvel_arbre": round(cout_nouveau, 2),
        "nb_aretes_nouvel_arbre": len(nouvel_arbre),
        "nouvel_arbre": nouvel_arbre,
    }
