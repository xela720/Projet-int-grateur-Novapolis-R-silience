"""Module 5 : Analyse de résilience et comparaison des scénarios de crise.

Ce module évalue l'impact des crises et perturbations sur le réseau de Novapolis :
- Situation normale (baseline de référence).
- Fermeture d'un axe routier important (ponts, autoroutes, tunnels).
- Panne de tronçon de fibre optique dorsale ou travaux.
- Crise multi-réseaux (ex : inondation).

Indicateurs clés de résilience (KPIs) calculés :
1. Nombre et proportion de demandes devenues inaccessibles.
2. Augmentation moyenne et maximale du temps de trajet des secours.
3. Évolution du nombre de composantes du réseau de fibre optique.
4. Coût du raccordement de remplacement ou de réparation.
5. Proportion des sites sensibles (hôpitaux, écoles, quartiers) restant accessibles.
"""

import os
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

import math
from typing import Dict, List, Any

from src.data_manager import ReseauNovapolis, appliquer_scenario
from src.accessibility import diagnostic_accessibilite
from src.shortest_paths import evaluer_demande_intervention
from src.spanning_tree import kruskal, simuler_panne_troncon


def evaluer_scenario(
    reseau_base: ReseauNovapolis, scenario_id: str, poids: str = "temps_normal"
) -> Dict[str, Any]:
    """Évalue un scénario spécifique et le compare à la référence normale.

    Garantit que la base n'est JAMAIS altérée (clonage strict).
    """
    # 1. Application de la perturbation sur une copie indépendante
    reseau_perturbe = appliquer_scenario(reseau_base, scenario_id)

    # 2. Diagnostic d'accessibilité post-crise
    diag_base = diagnostic_accessibilite(reseau_base.routier, reseau_base.fibre)
    diag_pert = diagnostic_accessibilite(reseau_perturbe.routier, reseau_perturbe.fibre)

    # 3. Évaluation de l'ensemble des demandes de secours
    evaluations_demandes = []
    demandes_inaccessibles = 0
    demandes_devenues_inaccessibles = 0
    augmentations_temps: List[float] = []

    for dem in reseau_base.demandes:
        ev = evaluer_demande_intervention(
            reseau_base.routier, reseau_perturbe.routier, dem, poids=poids
        )
        evaluations_demandes.append(ev)

        cout_av = ev["cout_avant"]
        cout_ap = ev["cout_apres"]

        if cout_ap is None:
            demandes_inaccessibles += 1
            if cout_av is not None:
                demandes_devenues_inaccessibles += 1
        elif cout_av is not None and cout_ap is not None:
            retard = max(0.0, cout_ap - cout_av)
            augmentations_temps.append(retard)

    total_demandes = len(reseau_base.demandes)
    hausse_moyenne = (
        sum(augmentations_temps) / len(augmentations_temps) if augmentations_temps else 0.0
    )
    hausse_maximale = max(augmentations_temps) if augmentations_temps else 0.0

    # 4. Évaluation du réseau de fibre optique (MST & pannes)
    mst_base = kruskal(reseau_base.fibre)
    mst_pert = kruskal(reseau_perturbe.fibre)

    cout_reparation = 0.0
    actions_scenario = reseau_base.scenarios.get(scenario_id, [])
    fibres_en_panne = [
        act for act in actions_scenario if act.type_element == "fibre" and act.action in ("fermer", "panne")
    ]

    # Si une arête de l'arbre a été touchée, simuler le coût de raccordement de remplacement
    for act in fibres_en_panne:
        paire = (act.u, act.v)
        try:
            res_panne = simuler_panne_troncon(reseau_base.fibre, mst_base["aretes"], paire)
            if res_panne["succes_reparation"] and res_panne["cout_remplacement"]:
                cout_reparation += res_panne["cout_remplacement"]
        except ValueError:
            # L'arête en panne ne faisait pas partie de l'arbre optimal
            pass

    return {
        "scenario_id": scenario_id,
        "total_demandes": total_demandes,
        "demandes_devenues_inaccessibles": demandes_devenues_inaccessibles,
        "pourcentage_demandes_perdues": round(
            (demandes_devenues_inaccessibles / total_demandes) * 100.0, 2
        ) if total_demandes else 0.0,
        "total_demandes_inaccessibles": demandes_inaccessibles,
        "hausse_moyenne_temps_min": round(hausse_moyenne, 2),
        "hausse_maximale_temps_min": round(hausse_maximale, 2),
        "sites_sensibles_accessibles_base": diag_base["nb_sensibles_accessibles"],
        "sites_sensibles_accessibles_pert": diag_pert["nb_sensibles_accessibles"],
        "proportion_sensibles_accessibles": diag_pert["taux_sensibles_accessibles"],
        "nb_composantes_fibre_base": diag_base["nb_composantes_fibre"],
        "nb_composantes_fibre_pert": diag_pert["nb_composantes_fibre"],
        "cout_mst_fibre_base": mst_base["cout_total"],
        "cout_mst_fibre_pert": mst_pert["cout_total"],
        "cout_reparation_estime": round(cout_reparation, 2),
        "evaluations_detaillees": evaluations_demandes,
    }


def comparer_tous_les_scenarios(
    reseau_base: ReseauNovapolis, poids: str = "temps_normal"
) -> Dict[str, Dict[str, Any]]:
    """Compare tous les scénarios configurés dans le fichier scenarios.csv."""
    rapport = {}
    for sc_id in reseau_base.scenarios.keys():
        rapport[sc_id] = evaluer_scenario(reseau_base, sc_id, poids=poids)
    return rapport


def afficher_tableau_resilience(rapport: Dict[str, Dict[str, Any]]):
    """Affiche un tableau récapitulatif formaté des indicateurs de résilience."""
    print("=" * 105)
    print(f"{'SCÉNARIO':<30} | {'DEM. PERDUES':<13} | {'RETARD MOY':<11} | {'RETARD MAX':<11} | {'SENSIBLES %':<12} | {'FIBRE COMP':<10}")
    print("-" * 105)

    for sc_id, res in rapport.items():
        dem_perdues = f"{res['demandes_devenues_inaccessibles']} ({res['pourcentage_demandes_perdues']}%)"
        retard_moy = f"+{res['hausse_moyenne_temps_min']} min"
        retard_max = f"+{res['hausse_maximale_temps_min']} min"
        sensibles = f"{round(res['proportion_sensibles_accessibles'] * 100, 1)}%"
        fibre_comp = f"{res['nb_composantes_fibre_pert']} ({res['cout_mst_fibre_pert']} k€)"

        print(
            f"{sc_id:<30} | {dem_perdues:<13} | {retard_moy:<11} | {retard_max:<11} | {sensibles:<12} | {fibre_comp:<10}"
        )
    print("=" * 105)
