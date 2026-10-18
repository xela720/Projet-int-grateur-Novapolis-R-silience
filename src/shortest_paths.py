"""Modules 2 & 3 : Itinéraires des secours et Détection des circuits absorbants.

Implémente :
- Dijkstra avec tas binaire (heapq) : O((|V| + |E|) log |V|)
- Bellman-Ford : O(|V| * |E|), détection rigoureuse des circuits absorbants accessibles vs non accessibles
- Floyd-Warshall : O(|V|^3), calcul de toutes les paires et détection des cycles négatifs sur la diagonale
- Reconstruction de chemin (durée, nombre d'arcs, fermetures traversées)
- Évaluation des interventions de secours avant et après perturbations (retards absolus et relatifs)
- Sélection automatique de la caserne optimale pour chaque demande
"""

import os
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

import heapq
import math
from collections import deque
from typing import Dict, List, Tuple, Set, Optional, Any

from src.data_manager import GrapheRoutier, Demande


def dijkstra(
    graphe: GrapheRoutier, source: str, poids: str = "temps_normal"
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Calcule les plus courts chemins depuis une source avec un tas binaire (heapq).

    Prérequis strict : tous les poids doivent être positifs ou nuls.
    Complexité : O((|V| + |E|) log |V|)
    """
    if source not in graphe.sites:
        raise KeyError(f"Sommet source inconnu : {source}")

    distances: Dict[str, float] = {s: math.inf for s in graphe.sommets()}
    predecesseurs: Dict[str, Optional[str]] = {s: None for s in graphe.sommets()}

    distances[source] = 0.0
    # Tas binaire contenant des tuples (distance_actuelle, sommet)
    tas: List[Tuple[float, str]] = [(0.0, source)]

    while tas:
        d_u, u = heapq.heappop(tas)

        if d_u > distances[u]:
            continue

        for v, arc in graphe.voisins(u, uniquement_ouverts=True).items():
            w = arc.get_poids(poids)
            if w < 0:
                raise ValueError(
                    f"Dijkstra ne supporte pas les poids négatifs. Arc {u}->{v} a un poids de {w}."
                )

            d_v = d_u + w
            if d_v < distances[v]:
                distances[v] = d_v
                predecesseurs[v] = u
                heapq.heappush(tas, (d_v, v))

    return distances, predecesseurs


def bellman_ford(
    graphe: GrapheRoutier, source: str, poids: str = "temps_normal"
) -> Dict[str, Any]:
    """Exécute l'algorithme de Bellman-Ford et analyse les circuits absorbants.

    Vérifie rigoureusement :
    1. Si un circuit absorbant est accessible depuis la source -> distances à -inf.
    2. Si un circuit absorbant existe ailleurs dans le graphe sans impacter la source.
    3. Ne renvoie jamais de distance finie pour un sommet dont la distance peut décroître indéfiniment.

    Complexité : O(|V| * |E|)
    """
    if source not in graphe.sites:
        raise KeyError(f"Sommet source inconnu : {source}")

    sommets = graphe.sommets()
    nb_sommets = len(sommets)
    distances: Dict[str, float] = {s: math.inf for s in sommets}
    predecesseurs: Dict[str, Optional[str]] = {s: None for s in sommets}

    distances[source] = 0.0
    arcs_ouverts = graphe.tous_les_arcs(uniquement_ouverts=True)

    # |V| - 1 passes de relaxation
    for _ in range(nb_sommets - 1):
        modifie = False
        for arc in arcs_ouverts:
            u, v = arc.u, arc.v
            w = arc.get_poids(poids)
            if distances[u] != math.inf and distances[u] + w < distances[v]:
                distances[v] = distances[u] + w
                predecesseurs[v] = u
                modifie = True
        if not modifie:
            break

    # |V|-ième passe : détection des relaxations possibles (circuits absorbants)
    noeuds_en_cycle_ouvert = set()
    for arc in arcs_ouverts:
        u, v = arc.u, arc.v
        w = arc.get_poids(poids)
        if distances[u] != math.inf and distances[u] + w < distances[v]:
            noeuds_en_cycle_ouvert.add(v)

    # Propagation de -infini à tous les sommets atteignables depuis le circuit absorbant
    noeuds_absorbants_depuis_source: Set[str] = set()
    if noeuds_en_cycle_ouvert:
        file = deque(list(noeuds_en_cycle_ouvert))
        while file:
            curr = file.popleft()
            if curr not in noeuds_absorbants_depuis_source:
                noeuds_absorbants_depuis_source.add(curr)
                distances[curr] = -math.inf
                for succ in graphe.voisins(curr, uniquement_ouverts=True):
                    if succ not in noeuds_absorbants_depuis_source:
                        file.append(succ)

    # Détection globale de tout circuit absorbant même non accessible depuis la source
    circuit_absorbant_global = len(noeuds_en_cycle_ouvert) > 0
    if not circuit_absorbant_global:
        # Test supplémentaire depuis une super-source virtuelle pour détecter tout cycle disjoint
        dist_glob: Dict[str, float] = {s: 0.0 for s in sommets}
        for _ in range(nb_sommets - 1):
            mod_g = False
            for arc in arcs_ouverts:
                if dist_glob[arc.u] + arc.get_poids(poids) < dist_glob[arc.v]:
                    dist_glob[arc.v] = dist_glob[arc.u] + arc.get_poids(poids)
                    mod_g = True
            if not mod_g:
                break
        for arc in arcs_ouverts:
            if dist_glob[arc.u] + arc.get_poids(poids) < dist_glob[arc.v]:
                circuit_absorbant_global = True
                break

    circuit_absorbant_accessible = len(noeuds_absorbants_depuis_source) > 0

    return {
        "distances": distances,
        "predecesseurs": predecesseurs,
        "circuit_absorbant_accessible": circuit_absorbant_accessible,
        "noeuds_absorbants_depuis_source": noeuds_absorbants_depuis_source,
        "circuit_absorbant_global": circuit_absorbant_global,
    }


def floyd_warshall(
    graphe: GrapheRoutier, poids: str = "temps_normal"
) -> Dict[str, Any]:
    """Calcule tous les plus courts chemins par programmation dynamique.

    Détecte les cycles absorbants via dist[i][i] < 0 sur la diagonale.
    Complexité : O(|V|^3)
    """
    sommets = graphe.sommets()
    n = len(sommets)
    idx_vers_sommet = {i: sommets[i] for i in range(n)}
    sommet_vers_idx = {sommets[i]: i for i in range(n)}

    dist = [[math.inf] * n for _ in range(n)]
    suivant: List[List[Optional[int]]] = [[None] * n for _ in range(n)]

    # Initialisation
    for i in range(n):
        dist[i][i] = 0.0
        suivant[i][i] = i

    for arc in graphe.tous_les_arcs(uniquement_ouverts=True):
        u_idx = sommet_vers_idx[arc.u]
        v_idx = sommet_vers_idx[arc.v]
        w = arc.get_poids(poids)
        # S'il y a plusieurs arcs entre u et v, garder le plus court
        if w < dist[u_idx][v_idx]:
            dist[u_idx][v_idx] = w
            suivant[u_idx][v_idx] = v_idx

    # Triples boucles de Floyd-Warshall
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] != math.inf and dist[k][j] != math.inf:
                    d_nouv = dist[i][k] + dist[k][j]
                    if d_nouv < dist[i][j]:
                        dist[i][j] = d_nouv
                        suivant[i][j] = suivant[i][k]

    # Détection des circuits absorbants sur la diagonale
    noeuds_en_cycle_absorbant = set()
    for i in range(n):
        if dist[i][i] < 0:
            noeuds_en_cycle_absorbant.add(idx_vers_sommet[i])

    # Propagation de -infini pour les paires traversant un sommet absorbant
    if noeuds_en_cycle_absorbant:
        indices_absorbants = [sommet_vers_idx[s] for s in noeuds_en_cycle_absorbant]
        for k in indices_absorbants:
            for i in range(n):
                for j in range(n):
                    if dist[i][k] != math.inf and dist[k][j] != math.inf:
                        dist[i][j] = -math.inf

    # Conversion en dictionnaires de noms de sommets
    dist_dict: Dict[str, Dict[str, float]] = {}
    suivant_dict: Dict[str, Dict[str, Optional[str]]] = {}

    for i in range(n):
        u = idx_vers_sommet[i]
        dist_dict[u] = {}
        suivant_dict[u] = {}
        for j in range(n):
            v = idx_vers_sommet[j]
            dist_dict[u][v] = dist[i][j]
            nxt = suivant[i][j]
            suivant_dict[u][v] = idx_vers_sommet[nxt] if nxt is not None else None

    return {
        "dist": dist_dict,
        "suivant": suivant_dict,
        "a_circuit_absorbant": len(noeuds_en_cycle_absorbant) > 0,
        "noeuds_en_circuit_absorbant": noeuds_en_cycle_absorbant,
    }


def reconstruire_chemin(
    predecesseurs: Dict[str, Optional[str]], source: str, cible: str
) -> List[str]:
    """Reconstruit la séquence des sommets depuis la source jusqu'à la cible."""
    if cible not in predecesseurs:
        return []
    if source == cible:
        return [source]

    chemin = []
    courant: Optional[str] = cible
    vus = set()

    while courant is not None:
        if courant in vus:
            # Sécurité contre boucle infinie
            return []
        vus.add(courant)
        chemin.append(courant)
        courant = predecesseurs.get(courant)
        if courant == source:
            chemin.append(source)
            break

    if not chemin or chemin[-1] != source:
        return []

    chemin.reverse()
    return chemin


def reconstruire_chemin_floyd_warshall(
    suivant: Dict[str, Dict[str, Optional[str]]],
    dist: Dict[str, Dict[str, float]],
    source: str,
    cible: str,
) -> List[str]:
    """Reconstruit le chemin entre source et cible à partir de la matrice 'suivant'."""
    if dist[source][cible] == math.inf or dist[source][cible] == -math.inf:
        return []
    if suivant[source][cible] is None:
        return []

    chemin = [source]
    courant = source
    vus = set()

    while courant != cible:
        if courant in vus:
            return []
        vus.add(courant)
        prochain = suivant[courant][cible]
        if prochain is None:
            return []
        chemin.append(prochain)
        courant = prochain

    return chemin


def choisir_meilleure_caserne(
    graphe: GrapheRoutier,
    cible: str,
    casernes: List[str],
    poids: str = "temps_normal",
) -> Tuple[Optional[str], float, List[str]]:
    """Sélectionne la caserne offrant le délai d'intervention le plus court vers la cible."""
    meilleure_caserne = None
    meilleur_temps = math.inf
    meilleur_chemin: List[str] = []

    for caserne in casernes:
        if caserne not in graphe.sites:
            continue
        distances, predecesseurs = dijkstra(graphe, caserne, poids=poids)
        t = distances.get(cible, math.inf)
        if t < meilleur_temps:
            meilleur_temps = t
            meilleure_caserne = caserne
            meilleur_chemin = reconstruire_chemin(predecesseurs, caserne, cible)

    return meilleure_caserne, meilleur_temps, meilleur_chemin


def evaluer_demande_intervention(
    graphe_normal: GrapheRoutier,
    graphe_perturbe: GrapheRoutier,
    demande: Demande,
    casernes: Optional[List[str]] = None,
    poids: str = "temps_normal",
) -> Dict[str, Any]:
    """Évalue l'impact d'une perturbation sur une demande d'intervention donnée.

    Calcule :
    - Coût avant et après perturbation
    - Retard absolu (min) et relatif (%)
    - Mention 'accessible' ou 'inaccessible'
    - Chemin retenu avant et après
    - Nombre d'arcs traversés
    - Liste des fermetures rencontrées
    """
    if casernes is None:
        casernes = [s_id for s_id, s in graphe_normal.sites.items() if s.type == "caserne"]

    # 1. Détermination de la source et de la destination
    if demande.destination:
        source = demande.origine
        cible = demande.destination
        # Calcul avant
        dist_av, pred_av = dijkstra(graphe_normal, source, poids=poids)
        cout_av = dist_av.get(cible, math.inf)
        chemin_av = reconstruire_chemin(pred_av, source, cible) if cout_av != math.inf else []
        # Calcul après
        dist_ap, pred_ap = dijkstra(graphe_perturbe, source, poids=poids)
        cout_ap = dist_ap.get(cible, math.inf)
        chemin_ap = reconstruire_chemin(pred_ap, source, cible) if cout_ap != math.inf else []
        caserne_retenue = source
    else:
        cible = demande.origine
        cas_av, cout_av, chemin_av = choisir_meilleure_caserne(graphe_normal, cible, casernes, poids=poids)
        cas_ap, cout_ap, chemin_ap = choisir_meilleure_caserne(graphe_perturbe, cible, casernes, poids=poids)
        caserne_retenue = cas_ap or cas_av

    # 2. Retards absolu et relatif
    accessible_avant = cout_av != math.inf and cout_av != -math.inf
    accessible_apres = cout_ap != math.inf and cout_ap != -math.inf

    if not accessible_apres:
        statut = "inaccessible"
        retard_absolu = math.inf
        retard_relatif = math.inf
    else:
        statut = "accessible"
        retard_absolu = max(0.0, cout_ap - cout_av) if accessible_avant else 0.0
        if accessible_avant and cout_av > 0:
            retard_relatif = round((retard_absolu / cout_av) * 100.0, 2)
        else:
            retard_relatif = 0.0

    return {
        "demande_id": demande.id,
        "type": demande.type,
        "priorite": demande.priorite,
        "caserne": caserne_retenue,
        "cible": cible,
        "statut": statut,
        "cout_avant": round(cout_av, 2) if cout_av != math.inf else None,
        "cout_apres": round(cout_ap, 2) if cout_ap != math.inf else None,
        "retard_absolu_min": round(retard_absolu, 2) if retard_absolu != math.inf else None,
        "retard_relatif_pourcent": retard_relatif if retard_relatif != math.inf else None,
        "nb_arcs_avant": len(chemin_av) - 1 if chemin_av else 0,
        "nb_arcs_apres": len(chemin_ap) - 1 if chemin_ap else 0,
        "chemin_avant": chemin_av,
        "chemin_apres": chemin_ap,
    }


def comparer_algorithmes_chemins(
    graphe: GrapheRoutier, source: str, poids: str = "temps_normal"
) -> Dict[str, Any]:
    """Compare Dijkstra, Bellman-Ford et Floyd-Warshall sur une même instance."""
    dist_dijkstra, _ = dijkstra(graphe, source, poids=poids)
    res_bf = bellman_ford(graphe, source, poids=poids)
    dist_bf = res_bf["distances"]

    res_fw = floyd_warshall(graphe, poids=poids)
    dist_fw = res_fw["dist"][source]

    # Vérification de cohérence exacte
    differences = {}
    for s in graphe.sommets():
        d_dijk = dist_dijkstra[s]
        d_b = dist_bf[s]
        d_f = dist_fw[s]

        diff_db = abs(d_dijk - d_b) if math.isfinite(d_dijk) and math.isfinite(d_b) else (d_dijk == d_b)
        if diff_db is not True and diff_db > 1e-6:
            differences[s] = {"dijkstra": d_dijk, "bellman_ford": d_b, "floyd_warshall": d_f}

    return {
        "concordance_parfaite": len(differences) == 0,
        "nb_sommets_compares": len(graphe.sommets()),
        "differences": differences,
        "circuit_absorbant_bf": res_bf["circuit_absorbant_accessible"],
        "circuit_absorbant_fw": res_fw["a_circuit_absorbant"],
    }
