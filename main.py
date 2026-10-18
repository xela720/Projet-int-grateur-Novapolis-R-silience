"""Interface en Ligne de Commande (CLI) pour Novapolis Résilience.

Point d'entrée principal du projet permettant de piloter l'ensemble des modules :
- Sélection du dossier de données (--data data/realiste, data/manuel, etc.)
- Sélection du scénario de perturbation (--scenario scenario_fermeture_pont)
- Choix de l'opération à exécuter (--operation diagnostic | itineraires | fibre | resilience | benchmark | visualize | all)
- Choix du régime de circulation (--poids temps_normal | temps_pointe)
"""

import os
import sys
import argparse

RACINE = os.path.abspath(os.path.dirname(__file__))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from src.data_manager import charger_reseau, appliquer_scenario
from src.accessibility import diagnostic_accessibilite, itineraire_min_arcs
from src.shortest_paths import (
    dijkstra,
    bellman_ford,
    floyd_warshall,
    evaluer_demande_intervention,
    comparer_algorithmes_chemins,
)
from src.spanning_tree import (
    kruskal,
    prim,
    comparer_kruskal_prim,
    simuler_panne_troncon,
)
from src.resilience import (
    evaluer_scenario,
    comparer_tous_les_scenarios,
    afficher_tableau_resilience,
)
from src.benchmarks import executer_benchmarks
from src.visualizer import (
    animer_dijkstra,
    visualiser_comparaison_itineraires,
    visualiser_fibre_et_reparation,
)


def afficher_banniere():
    print("=" * 80)
    print("           NOVAPOLIS RÉSILIENCE - OUTIL D'AIDE À LA DÉCISION URBAINE")
    print("        Optimisation des Secours et Infrastructure Réseau Résiliente")
    print("=" * 80)


def executer_diagnostic(reseau, args):
    print("\n--- [MODULE 1 : DIAGNOSTIC D'ACCESSIBILITÉ] ---")
    diag = diagnostic_accessibilite(reseau.routier, reseau.fibre)
    print(f"• Sites totaux répertoriés         : {diag['nb_sites_total']}")
    print(f"• Casernes d'intervention actives  : {len(diag['casernes_sources'])} ({', '.join(diag['casernes_sources'])})")
    print(f"• Sites accessibles depuis secours : {diag['nb_sites_accessibles_secours']} ({diag['taux_accessibilite_globale']*100:.1f}%)")
    print(f"• Sites sensibles accessibles      : {diag['nb_sensibles_accessibles']}/{diag['nb_sites_sensibles']} ({diag['taux_sensibles_accessibles']*100:.1f}%)")
    print(f"• Sites sans entrée (in-degree 0)  : {diag['sans_entree'] if diag['sans_entree'] else 'Aucun'}")
    print(f"• Culs-de-sac (out-degree 0)       : {diag['culs_de_sac'] if diag['culs_de_sac'] else 'Aucun'}")
    print(f"• Sites isolés                     : {diag['sites_isoles'] if diag['sites_isoles'] else 'Aucun'}")
    print(f"• Présence de cycles orientés      : {'OUI' if diag['presence_cycle_oriente'] else 'NON'}")
    if diag["presence_cycle_oriente"]:
        print(f"  -> Cycle orienté détecté         : {' -> '.join(diag['cycle_exemple'])}")
    print(f"• Composantes connexes fibre       : {diag['nb_composantes_fibre']} (Tailles: {diag['tailles_composantes_fibre']})")
    print(f"• Composantes fortement connexes   : {diag['nb_composantes_fortement_connexes']} (Principale: {diag['taille_principale_cfc']} sites)")


def executer_itineraires(reseau, args):
    print(f"\n--- [MODULE 2 : ITINÉRAIRES DES SECOURS & SCÉNARIO '{args.scenario}'] ---")
    reseau_perturbe = appliquer_scenario(reseau, args.scenario)

    print(f"{'DEMANDE':<10} | {'ORIGINE':<10} | {'DESTINATION':<12} | {'AVANT':<10} | {'APRÈS':<10} | {'RETARD':<12} | {'STATUT':<12}")
    print("-" * 85)

    for dem in reseau.demandes:
        ev = evaluer_demande_intervention(
            reseau.routier, reseau_perturbe.routier, dem, poids=args.poids
        )
        cout_av = f"{ev['cout_avant']} min" if ev['cout_avant'] is not None else "Inacc."
        cout_ap = f"{ev['cout_apres']} min" if ev['cout_apres'] is not None else "Inacc."
        retard = f"+{ev['retard_absolu_min']} min" if ev['retard_absolu_min'] is not None else "N/A"
        print(f"{dem.id:<10} | {dem.origine:<10} | {dem.destination or dem.origine:<12} | {cout_av:<10} | {cout_ap:<10} | {retard:<12} | {ev['statut']:<12}")


def executer_circuits_absorbants(reseau, args):
    print("\n--- [MODULE 3 : DÉTECTION DES CIRCUITS ABSORBANTS] ---")
    source = args.source if args.source else reseau.routier.sommets()[0]
    res_bf = bellman_ford(reseau.routier, source, poids=args.poids)
    print(f"• Source testée : {source}")
    print(f"• Circuit absorbant accessible depuis la source : {'OUI' if res_bf['circuit_absorbant_accessible'] else 'NON'}")
    print(f"• Circuit absorbant global dans le graphe       : {'OUI' if res_bf['circuit_absorbant_global'] else 'NON'}")
    if res_bf["circuit_absorbant_accessible"]:
        print(f"  -> Nœuds avec distance -infini (non finie)    : {res_bf['noeuds_absorbants_depuis_source']}")
    else:
        print("  -> Toutes les distances finies calculées sont stables et garanties.")


def executer_fibre(reseau, args):
    print("\n--- [MODULE 4 : CONCEPTION DU RÉSEAU DE FIBRE OPTIQUE] ---")
    comp = comparer_kruskal_prim(reseau.fibre)
    print(f"• Coût Arbre Couvrant (Kruskal) : {comp['cout_kruskal']} k€ ({comp['nb_aretes_kruskal']} tronçons)")
    print(f"• Coût Arbre Couvrant (Prim)    : {comp['cout_prim']} k€ ({comp['nb_aretes_prim']} tronçons)")
    print(f"• Égalité exacte des coûts      : {'OUI' if comp['couts_egaux'] else 'NON'}")
    if comp["explication_multiplicite"]:
        print(f"  Note : {comp['explication_multiplicite']}")

    res_k = kruskal(reseau.fibre)
    if res_k["aretes"]:
        premiere_arete = res_k["aretes"][0]
        paire_panne = premiere_arete.extremites()
        print(f"\n• Simulation de panne sur le tronçon {paire_panne} (coût original: {premiere_arete.cost} k€)...")
        res_panne = simuler_panne_troncon(reseau.fibre, res_k["aretes"], paire_panne)
        if res_panne["succes_reparation"]:
            print(f"  -> Raccordement de remplacement optimal : {res_panne['arete_remplacement']}")
            print(f"  -> Coût du nouveau câble               : {res_panne['cout_remplacement']} k€")
            print(f"  -> Surcoût total pour le réseau         : +{res_panne['surcout']} k€")
            print(f"  -> Nouveau coût de l'arbre réparé       : {res_panne['cout_total_nouvel_arbre']} k€")
        else:
            print("  -> Aucun câble de remplacement disponible dans le graphe initial (réseau scindé).")


def executer_resilience(reseau, args):
    print("\n--- [MODULE 5 : ANALYSE DE RÉSILIENCE COMPARATIVE MULTI-SCÉNARIOS] ---")
    rapport = comparer_tous_les_scenarios(reseau, poids=args.poids)
    afficher_tableau_resilience(rapport)


def executer_visuels(reseau, args):
    print("\n--- [BONUS VISUEL : GÉNÉRATION DES ANIMATIONS & SCHÉMAS] ---")
    os.makedirs("output", exist_ok=True)
    casernes = [s_id for s_id, s in reseau.routier.sites.items() if s.type == "caserne"]
    source = args.source or (casernes[0] if casernes else reseau.routier.sommets()[0])
    cibles = [s_id for s_id, s in reseau.routier.sites.items() if s.type in ("hopital", "ecole", "quartier")]
    cible = args.cible or (cibles[0] if cibles else reseau.routier.sommets()[-1])

    print(f"• Génération de l'animation Dijkstra : {source} -> {cible}...")
    animer_dijkstra(reseau.routier, source, cible, "output/demo_dijkstra.gif", fps=2)

    # Comparaison avant/après
    reseau_pert = appliquer_scenario(reseau, args.scenario if args.scenario != "scenario_normal" else "scenario_fermeture_pont")
    _, p_av = dijkstra(reseau.routier, source, poids=args.poids)
    _, p_ap = dijkstra(reseau_pert.routier, source, poids=args.poids)
    from src.shortest_paths import reconstruire_chemin
    ch_av = reconstruire_chemin(p_av, source, cible)
    ch_ap = reconstruire_chemin(p_ap, source, cible)

    routes_fermees = []
    for u in reseau.routier.adj:
        for v, arc in reseau.routier.adj[u].items():
            if arc.est_ouvert() and not reseau_pert.routier.adj[u][v].est_ouvert():
                routes_fermees.append((u, v))

    print("• Génération de la comparaison graphique avant/après crise...")
    visualiser_comparaison_itineraires(
        reseau.routier, reseau_pert.routier, ch_av, ch_ap, routes_fermees, "output/comparaison_avant_apres.png"
    )

    # Réparation fibre
    res_k = kruskal(reseau.fibre)
    if res_k["aretes"]:
        panne = res_k["aretes"][0].extremites()
        res_p = simuler_panne_troncon(reseau.fibre, res_k["aretes"], panne)
        print("• Génération du schéma de résilience fibre...")
        visualiser_fibre_et_reparation(
            reseau.fibre, res_k["aretes"], panne, res_p["arete_remplacement"], "output/reparation_fibre.png"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Novapolis Résilience : Outil en ligne de commande pour l'optimisation des secours et du réseau."
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/realiste",
        help="Chemin vers le dossier contenant les fichiers CSV (ex: data/realiste, data/manuel)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="scenario_normal",
        help="Nom du scénario à appliquer (ex: scenario_normal, scenario_fermeture_pont, scenario_inondation_sud)",
    )
    parser.add_argument(
        "--operation",
        type=str,
        default="all",
        choices=["diagnostic", "itineraires", "circuits_absorbants", "fibre", "resilience", "benchmark", "visualize", "all"],
        help="Opération à exécuter",
    )
    parser.add_argument(
        "--poids",
        type=str,
        default="temps_normal",
        choices=["temps_normal", "temps_pointe"],
        help="Poids routier utilisé pour les calculs d'itinéraires",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Sommet source pour les calculs de plus court chemin ou parcours",
    )
    parser.add_argument(
        "--cible",
        type=str,
        default=None,
        help="Sommet destination pour les calculs de plus court chemin",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Lance le menu interactif en direct dans la console",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Lance le tableau de bord web interactif en temps réel (HTML5/Canvas)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port pour le serveur web interactif (défaut: 8000)",
    )

    args = parser.parse_args()
    afficher_banniere()

    if args.interactive:
        from src.interactive_cli import menu_interactif
        menu_interactif()
        return

    if args.web:
        from src.web_dashboard import lancer_serveur
        lancer_serveur(args.port)
        return

    if args.operation == "benchmark":
        executer_benchmarks(repetitions=5, seed=42)
        return

    print(f"Chargement des données depuis '{args.data}'...")
    try:
        reseau = charger_reseau(args.data)
        print(f"Données chargées : {len(reseau.routier.sommets())} sites, {len(reseau.routier.tous_les_arcs())} routes, {len(reseau.fibre.toutes_les_aretes())} tronçons fibre.")
    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        sys.exit(1)

    if args.operation in ("diagnostic", "all"):
        executer_diagnostic(reseau, args)

    if args.operation in ("itineraires", "all"):
        executer_itineraires(reseau, args)

    if args.operation in ("circuits_absorbants", "all"):
        executer_circuits_absorbants(reseau, args)

    if args.operation in ("fibre", "all"):
        executer_fibre(reseau, args)

    if args.operation in ("resilience", "all"):
        executer_resilience(reseau, args)

    if args.operation in ("visualize", "all"):
        executer_visuels(reseau, args)

    print("\n" + "=" * 80)
    print("EXÉCUTION TERMINÉE AVEC SUCCÈS.")
    print("=" * 80)


if __name__ == "__main__":
    main()
