"""Module 1 : Diagnostic d'accessibilité pour Novapolis Résilience.

Implémente :
- Parcours en profondeur (DFS) et en largeur (BFS).
- Accessibilité depuis une ou plusieurs sources (casernes, hôpitaux).
- Itinéraire minimisant le nombre d'arcs (BFS).
- Identification des composantes connexes du réseau de fibre optique.
- Détection des cycles orientés dans le réseau routier (algorithme 3 couleurs).
- Calcul des composantes fortement connexes (Tarjan) et faiblement connexes.
- Détection rigoureuse des sites isolés, culs-de-sac et sites non atteignables.
- Distinction théorique claire entre connexité ordinaire, accessibilité depuis une source et forte connexité.
"""

import os
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from collections import deque
from typing import Dict, List, Set, Tuple, Optional, Any
from src.data_manager import GrapheRoutier, GrapheFibre


def dfs_parcours(graphe: GrapheRoutier, source: str, visites: Optional[Set[str]] = None) -> Set[str]:
    """Effectue un parcours en profondeur (DFS) itératif depuis une source.

    Complexité : O(|V| + |E|)
    """
    if source not in graphe.sites:
        raise KeyError(f"Sommet source inconnu : {source}")

    if visites is None:
        visites = set()

    pile = [source]
    while pile:
        sommet = pile.pop()
        if sommet not in visites:
            visites.add(sommet)
            # Ajoute les voisins ouverts
            for voisin in graphe.voisins(sommet, uniquement_ouverts=True):
                if voisin not in visites:
                    pile.append(voisin)
    return visites


def bfs_parcours(
    graphe: GrapheRoutier, source: str
) -> Tuple[Dict[str, int], Dict[str, Optional[str]]]:
    """Effectue un parcours en largeur (BFS) depuis une source.

    Renvoie :
    - dist_sauts : dictionnaire {sommet: nombre_minimal_d_arcs}
    - predecesseurs : dictionnaire {sommet: predecesseur} pour reconstruction

    Complexité : O(|V| + |E|)
    """
    if source not in graphe.sites:
        raise KeyError(f"Sommet source inconnu : {source}")

    dist_sauts = {source: 0}
    predecesseurs: Dict[str, Optional[str]] = {source: None}
    file = deque([source])

    while file:
        u = file.popleft()
        d_actuelle = dist_sauts[u]
        for v in graphe.voisins(u, uniquement_ouverts=True):
            if v not in dist_sauts:
                dist_sauts[v] = d_actuelle + 1
                predecesseurs[v] = u
                file.append(v)

    return dist_sauts, predecesseurs


def accessibilite_multi_sources(
    graphe: GrapheRoutier, sources: List[str]
) -> Set[str]:
    """Calcule l'ensemble des sites accessibles depuis au moins une des sources fournies.

    Utilise une file BFS multi-sources initialisée avec toutes les casernes.
    Complexité : O(|V| + |E|)
    """
    visites = set()
    file = deque()

    for s in sources:
        if s in graphe.sites:
            visites.add(s)
            file.append(s)

    while file:
        u = file.popleft()
        for v in graphe.voisins(u, uniquement_ouverts=True):
            if v not in visites:
                visites.add(v)
                file.append(v)

    return visites


def itineraire_min_arcs(
    graphe: GrapheRoutier, source: str, cible: str
) -> Optional[Dict[str, Any]]:
    """Calcule un itinéraire minimisant strictement le nombre d'arcs via BFS.

    Renvoie un dictionnaire détaillant le chemin, le nombre d'arcs et la durée cumulée.
    """
    if source not in graphe.sites or cible not in graphe.sites:
        return None

    dist_sauts, predecesseurs = bfs_parcours(graphe, source)
    if cible not in dist_sauts:
        return None

    # Reconstruction du chemin
    chemin = []
    courant: Optional[str] = cible
    while courant is not None:
        chemin.append(courant)
        courant = predecesseurs[courant]
    chemin.reverse()

    # Calcul des durées cumulées
    duree_normale = 0.0
    duree_pointe = 0.0
    for i in range(len(chemin) - 1):
        arc = graphe.adj[chemin[i]][chemin[i + 1]]
        duree_normale += arc.temps_normal
        duree_pointe += arc.temps_pointe

    return {
        "chemin": chemin,
        "nb_arcs": dist_sauts[cible],
        "temps_normal": round(duree_normale, 2),
        "temps_pointe": round(duree_pointe, 2),
    }


def composantes_connexes_fibre(graphe_fibre: GrapheFibre) -> List[Set[str]]:
    """Identifie les composantes connexes du réseau de fibre (graphe non orienté).

    Complexité : O(|V| + |E|)
    """
    visites = set()
    composantes = []

    for site_id in graphe_fibre.sommets():
        if site_id not in visites:
            comp = set()
            file = deque([site_id])
            visites.add(site_id)
            while file:
                u = file.popleft()
                comp.add(u)
                for v in graphe_fibre.voisins(u, uniquement_actifs=True):
                    if v not in visites:
                        visites.add(v)
                        file.append(v)
            composantes.append(comp)

    # Tri par taille décroissante
    composantes.sort(key=len, reverse=True)
    return composantes


def detecter_cycles_orientes(graphe: GrapheRoutier) -> Tuple[bool, List[str]]:
    """Détecte la présence d'un cycle orienté dans le réseau routier.

    Utilise l'algorithme des trois couleurs (DFS) :
    - 0 (Blanc) : sommet non visité
    - 1 (Gris) : sommet en cours d'exploration (dans la pile de récursion)
    - 2 (Noir) : sommet complètement exploré

    Renvoie :
    - (True, cycle_trouve) si un cycle orienté existe.
    - (False, []) sinon.

    Complexité : O(|V| + |E|)
    """
    couleur: Dict[str, int] = {s: 0 for s in graphe.sommets()}
    parent: Dict[str, Optional[str]] = {s: None for s in graphe.sommets()}
    cycle_trouve: List[str] = []

    def dfs_visite(u: str) -> bool:
        nonlocal cycle_trouve
        couleur[u] = 1  # Gris
        for v in graphe.voisins(u, uniquement_ouverts=True):
            if couleur[v] == 1:
                # Arc arrière détecté : cycle trouvé !
                cycle = [v, u]
                curr = parent[u]
                while curr is not None and curr != v:
                    cycle.append(curr)
                    curr = parent[curr]
                cycle.append(v)
                cycle.reverse()
                cycle_trouve = cycle
                return True
            elif couleur[v] == 0:
                parent[v] = u
                if dfs_visite(v):
                    return True
        couleur[u] = 2  # Noir
        return False

    for s in graphe.sommets():
        if couleur[s] == 0:
            if dfs_visite(s):
                return True, cycle_trouve

    return False, []


def composantes_fortement_connexes(graphe: GrapheRoutier) -> List[Set[str]]:
    """Calcule les composantes fortement connexes (CFC) via l'algorithme de Tarjan.

    Dans un graphe orienté, deux sommets u et v appartiennent à la même CFC
    si et seulement s'il existe un chemin orienté de u vers v ET un chemin orienté de v vers u.

    Complexité : O(|V| + |E|)
    """
    index = 0
    indices: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    sur_pile: Dict[str, bool] = {}
    pile: List[str] = []
    cfc_liste: List[Set[str]] = []

    def strongconnect(u: str):
        nonlocal index
        indices[u] = index
        lowlink[u] = index
        index += 1
        pile.append(u)
        sur_pile[u] = True

        for v in graphe.voisins(u, uniquement_ouverts=True):
            if v not in indices:
                strongconnect(v)
                lowlink[u] = min(lowlink[u], lowlink[v])
            elif sur_pile.get(v, False):
                lowlink[u] = min(lowlink[u], indices[v])

        if lowlink[u] == indices[u]:
            nouvelle_cfc = set()
            while True:
                w = pile.pop()
                sur_pile[w] = False
                nouvelle_cfc.add(w)
                if w == u:
                    break
            cfc_liste.append(nouvelle_cfc)

    for s in graphe.sommets():
        if s not in indices:
            strongconnect(s)

    cfc_liste.sort(key=len, reverse=True)
    return cfc_liste


def composantes_faiblement_connexes(graphe: GrapheRoutier) -> List[Set[str]]:
    """Calcule les composantes faiblement connexes (connexité ordinaire).

    Considère les arcs orientés comme des arêtes non orientées.
    Complexité : O(|V| + |E|)
    """
    visites = set()
    composantes = []

    for s in graphe.sommets():
        if s not in visites:
            comp = set()
            file = deque([s])
            visites.add(s)
            while file:
                u = file.popleft()
                comp.add(u)
                voisins_totaux = set(graphe.voisins(u, uniquement_ouverts=True).keys()) | set(
                    graphe.voisins_entrants(u, uniquement_ouverts=True).keys()
                )
                for v in voisins_totaux:
                    if v not in visites:
                        visites.add(v)
                        file.append(v)
            composantes.append(comp)

    composantes.sort(key=len, reverse=True)
    return composantes


def diagnostic_accessibilite(
    graphe_routier: GrapheRoutier,
    graphe_fibre: GrapheFibre,
    types_sources: Tuple[str, ...] = ("caserne",),
) -> Dict[str, Any]:
    """Exécute un audit complet d'accessibilité et de résilience structurelle.

    Retourne un dictionnaire complet des indicateurs :
    - Sites isolés (degré entrant et sortant = 0)
    - Culs-de-sac sans sortie (degré sortant = 0)
    - Sites sans entrée (in-degree = 0)
    - Sites inatteignables depuis l'ensemble des casernes
    - Proportion des sites sensibles (hôpitaux, écoles, quartiers) accessibles
    - Composantes connexes de la fibre
    - Détection de cycles orientés
    - Analyse comparée des 3 types de connexité :
      * Connexité ordinaire (faible)
      * Accessibilité orientée depuis les secours
      * Connexité forte (SCC)
    """
    tous_les_sites = graphe_routier.sommets()
    nb_sites = len(tous_les_sites)

    # 1. Identification des casernes sources
    sources_casernes = [
        s_id for s_id, s in graphe_routier.sites.items() if s.type in types_sources
    ]

    # 2. Accessibilité depuis les casernes
    accessibles_casernes = accessibilite_multi_sources(graphe_routier, sources_casernes)
    non_atteignables_secours = set(tous_les_sites) - accessibles_casernes

    # 3. Degrés des sommets
    sites_isoles = []
    culs_de_sac = []
    sans_entree = []

    for s in tous_les_sites:
        deg_sortant = len(graphe_routier.voisins(s, uniquement_ouverts=True))
        deg_entrant = len(graphe_routier.voisins_entrants(s, uniquement_ouverts=True))

        if deg_sortant == 0 and deg_entrant == 0:
            sites_isoles.append(s)
        elif deg_sortant == 0:
            culs_de_sac.append(s)
        elif deg_entrant == 0:
            sans_entree.append(s)

    # 4. Accessibilité des sites sensibles
    sites_sensibles = [
        s_id for s_id, s in graphe_routier.sites.items() if s.type in ("hopital", "ecole", "quartier")
    ]
    sensibles_accessibles = [s for s in sites_sensibles if s in accessibles_casernes]
    taux_sensibles_accessibles = (
        len(sensibles_accessibles) / len(sites_sensibles) if sites_sensibles else 1.0
    )

    # 5. Cycles orientés
    a_cycle, cycle_exemple = detecter_cycles_orientes(graphe_routier)

    # 6. Fibre optique
    comp_fibre = composantes_connexes_fibre(graphe_fibre)

    # 7. Connexités orientées
    scc = composantes_fortement_connexes(graphe_routier)
    wcc = composantes_faiblement_connexes(graphe_routier)

    return {
        "nb_sites_total": nb_sites,
        "casernes_sources": sources_casernes,
        "nb_sites_accessibles_secours": len(accessibles_casernes),
        "taux_accessibilite_globale": round(len(accessibles_casernes) / nb_sites, 4) if nb_sites else 0.0,
        "sites_non_atteignables_secours": sorted(list(non_atteignables_secours)),
        "nb_sites_sensibles": len(sites_sensibles),
        "nb_sensibles_accessibles": len(sensibles_accessibles),
        "taux_sensibles_accessibles": round(taux_sensibles_accessibles, 4),
        "sites_isoles": sorted(sites_isoles),
        "culs_de_sac": sorted(culs_de_sac),
        "sans_entree": sorted(sans_entree),
        "presence_cycle_oriente": a_cycle,
        "cycle_exemple": cycle_exemple,
        "nb_composantes_fibre": len(comp_fibre),
        "tailles_composantes_fibre": [len(c) for c in comp_fibre],
        "nb_composantes_fortement_connexes": len(scc),
        "taille_principale_cfc": len(scc[0]) if scc else 0,
        "nb_composantes_faiblement_connexes": len(wcc),
    }
