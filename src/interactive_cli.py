"""Mode Console Interactif en Temps Réel pour Novapolis Résilience.

Permet au professeur ou à l'évaluateur de piloter l'application en direct :
- Sélectionner interactivement le jeu de données et le scénario.
- Choisir les points d'origine et de destination.
- Visualiser les résultats en temps réel dans une fenêtre Matplotlib interactive (avec zoom, pan et clics).
- Lancer l'animation dynamique de propagation des secours en direct.
"""

import os
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

import math
import matplotlib.pyplot as plt

from src.data_manager import charger_reseau, appliquer_scenario
from src.accessibility import diagnostic_accessibilite, itineraire_min_arcs
from src.shortest_paths import dijkstra, bellman_ford, reconstruire_chemin, evaluer_demande_intervention
from src.spanning_tree import kruskal, prim, simuler_panne_troncon
from src.resilience import comparer_tous_les_scenarios, afficher_tableau_resilience


def menu_interactif():
    dossier_data = "data/realiste"
    scenario_actuel = "scenario_normal"
    reseau_base = charger_reseau(dossier_data)

    while True:
        print("\n" + "=" * 75)
        print("         NOVAPOLIS RÉSILIENCE : MENU INTERACTIF EN TEMPS RÉEL")
        print("=" * 75)
        print(f"  Configuration active :")
        print(f"  • Réseau   : {dossier_data} ({len(reseau_base.routier.sommets())} sites)")
        print(f"  • Scénario : {scenario_actuel}")
        print("-" * 75)
        print("  1. Changer de jeu de données (manuel, réaliste, synthétique, absorbant)")
        print("  2. Choisir un scénario de crise (fermeture de pont, inondation, panne)")
        print("  3. Exécuter le diagnostic d'accessibilité en direct (Module 1)")
        print("  4. Calculer un itinéraire d'urgence interactif (Module 2)")
        print("  5. Tester la détection de circuit absorbant (Module 3)")
        print("  6. Optimiser la fibre (Kruskal/Prim) et simuler une panne (Module 4)")
        print("  7. Afficher le tableau de bord de résilience complet (Module 5)")
        print("  8. [TEMPS RÉEL] Ouvrir la carte interactive avec Zoom, Pan et Clics")
        print("  9. [TEMPS RÉEL] Lancer l'animation dynamique de Dijkstra à l'écran")
        print("  0. Quitter")
        print("=" * 75)

        choix = input("Votre choix [0-9] : ").strip()

        if choix == "0":
            print("\nFermeture du menu interactif. Au revoir !")
            break

        elif choix == "1":
            print("\nJeux de données disponibles :")
            print("  [1] data/manuel (8 sites, vérifiable sur papier)")
            print("  [2] data/realiste (110 sites, 5 districts)")
            print("  [3] data/synthetique (1000 sites, benchmark)")
            print("  [4] data/test_absorbant_accessible (circuit absorbant accessible)")
            print("  [5] data/test_absorbant_non_accessible (circuit absorbant non accessible)")
            c_data = input("Sélectionnez le jeu [1-5] (défaut 2) : ").strip()
            table_d = {
                "1": "data/manuel",
                "2": "data/realiste",
                "3": "data/synthetique",
                "4": "data/test_absorbant_accessible",
                "5": "data/test_absorbant_non_accessible",
            }
            dossier_data = table_d.get(c_data, "data/realiste")
            print(f"Chargement de {dossier_data}...")
            reseau_base = charger_reseau(dossier_data)
            scenario_actuel = "scenario_normal"
            print("Données chargées avec succès !")

        elif choix == "2":
            scenarios = list(reseau_base.scenarios.keys())
            if not scenarios:
                print("Aucun scénario configuré dans ce jeu.")
                continue
            print("\nScénarios disponibles pour ce jeu :")
            for idx, sc in enumerate(scenarios, start=1):
                print(f"  [{idx}] {sc}")
            c_sc = input(f"Choisissez un scénario [1-{len(scenarios)}] : ").strip()
            try:
                idx_choisi = int(c_sc) - 1
                if 0 <= idx_choisi < len(scenarios):
                    scenario_actuel = scenarios[idx_choisi]
                    print(f"Scénario actif : {scenario_actuel}")
                else:
                    print("Choix invalide.")
            except ValueError:
                print("Entrée non numérique.")

        elif choix == "3":
            print("\n--- DIAGNOSTIC D'ACCESSIBILITÉ ---")
            diag = diagnostic_accessibilite(reseau_base.routier, reseau_base.fibre)
            print(f"• Total sites répertoriés   : {diag['nb_sites_total']}")
            print(f"• Casernes d'intervention    : {', '.join(diag['casernes_sources'])}")
            print(f"• Taux d'accès secours       : {diag['taux_accessibilite_globale']*100:.1f}%")
            print(f"• Sites sensibles couverts   : {diag['nb_sensibles_accessibles']}/{diag['nb_sites_sensibles']} ({diag['taux_sensibles_accessibles']*100:.1f}%)")
            print(f"• Culs-de-sac sans sortie    : {diag['culs_de_sac'] if diag['culs_de_sac'] else 'Aucun'}")
            print(f"• Sites sans entrée          : {diag['sans_entree'] if diag['sans_entree'] else 'Aucun'}")
            print(f"• Composantes fibre          : {diag['nb_composantes_fibre']}")
            print(f"• Présence cycles orientés   : {diag['presence_cycle_oriente']}")
            input("\nAppuyez sur Entrée pour revenir au menu...")

        elif choix == "4":
            casernes = [s_id for s_id, s in reseau_base.routier.sites.items() if s.type == "caserne"]
            cibles = [s_id for s_id, s in reseau_base.routier.sites.items() if s.type in ("hopital", "ecole", "quartier")]

            dep_defaut = casernes[0] if casernes else reseau_base.routier.sommets()[0]
            arr_defaut = cibles[0] if cibles else reseau_base.routier.sommets()[-1]

            print(f"\nExemples de casernes : {', '.join(casernes[:5])}")
            print(f"Exemples de cibles   : {', '.join(cibles[:5])}")

            dep = input(f"Point de départ / Caserne (défaut {dep_defaut}) : ").strip() or dep_defaut
            arr = input(f"Point d'arrivée / Cible   (défaut {arr_defaut}) : ").strip() or arr_defaut

            if dep not in reseau_base.routier.sites or arr not in reseau_base.routier.sites:
                print("Erreur : l'un des sommets spécifiés n'existe pas.")
                continue

            # Calcul situation normale
            dist_norm, pred_norm = dijkstra(reseau_base.routier, dep)
            ch_norm = reconstruire_chemin(pred_norm, dep, arr)
            t_norm = dist_norm.get(arr, math.inf)

            # Calcul situation sous scénario
            reseau_pert = appliquer_scenario(reseau_base, scenario_actuel)
            dist_pert, pred_pert = dijkstra(reseau_pert.routier, dep)
            ch_pert = reconstruire_chemin(pred_pert, dep, arr)
            t_pert = dist_pert.get(arr, math.inf)

            print("\nRésultats de la simulation :")
            print(f"• Situation NORMALE :")
            if t_norm != math.inf:
                print(f"  -> Durée : {t_norm:.2f} min | {len(ch_norm)-1} arcs")
                print(f"  -> Chemin: {' -> '.join(ch_norm[:8])}{' ...' if len(ch_norm)>8 else ''}")
            else:
                print("  -> Inaccessible !")

            print(f"• Situation SCÉNARIO '{scenario_actuel}' :")
            if t_pert != math.inf:
                retard = t_pert - t_norm if t_norm != math.inf else 0.0
                print(f"  -> Durée : {t_pert:.2f} min | {len(ch_pert)-1} arcs")
                print(f"  -> Retard subi : +{retard:.2f} min ({(retard/t_norm)*100:.1f}%)" if t_norm > 0 else "")
                print(f"  -> Chemin: {' -> '.join(ch_pert[:8])}{' ...' if len(ch_pert)>8 else ''}")
            else:
                print("  -> ALERTE : Le site est devenu INACCESSIBLE suite aux perturbations !")

            input("\nAppuyez sur Entrée pour revenir au menu...")

        elif choix == "5":
            print(f"\n--- DÉTECTION DES CIRCUITS ABSORBANTS SUR '{dossier_data}' ---")
            source = reseau_base.routier.sommets()[0]
            res_bf = bellman_ford(reseau_base.routier, source)
            print(f"• Source testée : {source}")
            print(f"• Présence d'un circuit absorbant accessible depuis la source : {res_bf['circuit_absorbant_accessible']}")
            print(f"• Présence globale d'un circuit absorbant dans le réseau     : {res_bf['circuit_absorbant_global']}")
            if res_bf["circuit_absorbant_accessible"]:
                print(f"  -> Sommets dont la distance devient -infini : {res_bf['noeuds_absorbants_depuis_source']}")
            else:
                print("  -> Les temps de parcours sont stables (aucun cycle infini).")
            input("\nAppuyez sur Entrée pour revenir au menu...")

        elif choix == "6":
            print("\n--- OPTIMISATION DU RÉSEAU DE FIBRE OPTIQUE ---")
            res_k = kruskal(reseau_base.fibre)
            res_p = prim(reseau_base.fibre)
            print(f"• Arbre couvrant minimal (Kruskal) : {res_k['cout_total']} k€ ({len(res_k['aretes'])} câbles)")
            print(f"• Arbre couvrant minimal (Prim)    : {res_p['cout_total']} k€ ({len(res_p['aretes'])} câbles)")
            print(f"• Concordance mathématique exacte  : {abs(res_k['cout_total'] - res_p['cout_total']) < 1e-4}")

            if res_k["aretes"]:
                premiere = res_k["aretes"][0].extremites()
                print(f"\nSimulation de panne sur le câble dorsal {premiere}...")
                res_panne = simuler_panne_troncon(reseau_base.fibre, res_k["aretes"], premiere)
                if res_panne["succes_reparation"]:
                    print(f"  -> Câble de secours optimal : {res_panne['arete_remplacement']}")
                    print(f"  -> Coût du nouveau tronçon  : {res_panne['cout_remplacement']} k€")
                    print(f"  -> Surcoût pour le budget   : +{res_panne['surcout']} k€")
                    print(f"  -> Nouveau coût de l'arbre  : {res_panne['cout_total_nouvel_arbre']} k€")
            input("\nAppuyez sur Entrée pour revenir au menu...")

        elif choix == "7":
            print("\n--- TABLEAU COMPARATIF DES SCÉNARIOS DE CRISE ---")
            rapport = comparer_tous_les_scenarios(reseau_base)
            afficher_tableau_resilience(rapport)
            input("\nAppuyez sur Entrée pour revenir au menu...")

        elif choix == "8":
            print("\nOuverture de la fenêtre interactive Matplotlib...")
            print("Astuce : Utilisez la loupe pour zoomer et la croix pour déplacer la carte !")
            ouvrir_carte_interactive(reseau_base, scenario_actuel)

        elif choix == "9":
            print("\nLancement de l'animation en direct...")
            casernes = [s_id for s_id, s in reseau_base.routier.sites.items() if s.type == "caserne"]
            dep = casernes[0] if casernes else reseau_base.routier.sommets()[0]
            arr = reseau_base.routier.sommets()[-1]
            lancer_animation_directe(reseau_base.routier, dep, arr)


def ouvrir_carte_interactive(reseau_base, scenario_id):
    """Ouvre une fenêtre graphique Matplotlib interactive avec pan/zoom et info-bulles."""
    reseau_pert = appliquer_scenario(reseau_base, scenario_id)
    positions = {s_id: (s.longitude, s.latitude) for s_id, s in reseau_base.routier.sites.items()}

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.canvas.manager.set_window_title(f"Novapolis Résilience : Carte Interactive ({scenario_id})")
    ax.set_facecolor("#1e1e24")
    fig.patch.set_facecolor("#1e1e24")

    # 1. Tracé des routes normales
    for arc in reseau_base.routier.tous_les_arcs():
        if arc.u in positions and arc.v in positions:
            x1, y1 = positions[arc.u]
            x2, y2 = positions[arc.v]
            ax.plot([x1, x2], [y1, y2], color="#444455", linewidth=1.0, zorder=1)

    # 2. Tracé des routes fermées par le scénario
    fermetures = []
    for u in reseau_base.routier.adj:
        for v, arc in reseau_base.routier.adj[u].items():
            if arc.est_ouvert() and not reseau_pert.routier.adj[u][v].est_ouvert():
                fermetures.append((u, v))
                x1, y1 = positions[u]
                x2, y2 = positions[v]
                ax.plot([x1, x2], [y1, y2], color="#e74c3c", linewidth=3.5, linestyle="--", zorder=3)

    # 3. Tracé des sommets par type
    couleurs_types = {
        "caserne": "#e74c3c",
        "hopital": "#2ecc71",
        "telecom": "#3498db",
        "ecole": "#9b59b6",
        "quartier": "#f39c12",
    }

    for t, col in couleurs_types.items():
        sites_t = [s for s in reseau_base.routier.sites.values() if s.type == t]
        if sites_t:
            xs = [s.longitude for s in sites_t]
            ys = [s.latitude for s in sites_t]
            ax.scatter(xs, ys, color=col, s=70, label=f"{t.capitalize()} ({len(sites_t)})", zorder=4)

    # Sites spéciaux
    autres = [s for s in reseau_base.routier.sites.values() if s.type not in couleurs_types]
    if autres:
        ax.scatter([s.longitude for s in autres], [s.latitude for s in autres], color="#95a5a6", s=50, label="Autres sites", zorder=4)

    if fermetures:
        ax.plot([], [], color="#e74c3c", linewidth=3.0, linestyle="--", label=f"Axes coupés ({len(fermetures)})")

    ax.set_title(f"Novapolis : Vue Interactive en Temps Réel (Scénario : {scenario_id})", color="white", fontsize=13, fontweight="bold")
    ax.set_xlabel("Longitude (Déplacez et zoomez à la souris)", color="white")
    ax.set_ylabel("Latitude", color="white")
    ax.tick_params(colors="white")
    ax.legend(loc="upper right", facecolor="#2c2c34", edgecolor="none", labelcolor="white")

    plt.tight_layout()
    plt.show()


def lancer_animation_directe(graphe_routier, source, cible):
    """Lance à l'écran l'animation de Dijkstra en direct dans une fenêtre Matplotlib interactive."""
    import matplotlib.animation as animation
    positions = {s_id: (s.longitude, s.latitude) for s_id, s in graphe_routier.sites.items()}

    distances, predecesseurs = dijkstra(graphe_routier, source)
    chemin = reconstruire_chemin(predecesseurs, source, cible)

    fig, ax = plt.subplots(figsize=(11, 7.5))
    fig.canvas.manager.set_window_title(f"Simulation Temps Réel : Secours {source} -> {cible}")

    def update(frame):
        ax.clear()
        ax.set_facecolor("#1e1e24")
        fig.patch.set_facecolor("#1e1e24")

        # Fond du réseau
        for arc in graphe_routier.tous_les_arcs():
            if arc.u in positions and arc.v in positions:
                ax.plot([positions[arc.u][0], positions[arc.v][0]],
                        [positions[arc.u][1], positions[arc.v][1]],
                        color="#444455", linewidth=1.0, zorder=1)

        # Sommets
        ax.scatter([pos[0] for pos in positions.values()],
                   [pos[1] for pos in positions.values()],
                   color="#777788", s=30, zorder=2)

        # Progression du véhicule sur le chemin
        limite = min(frame + 1, len(chemin))
        for i in range(limite - 1):
            u_p, v_p = chemin[i], chemin[i + 1]
            ax.plot([positions[u_p][0], positions[v_p][0]],
                    [positions[u_p][1], positions[v_p][1]],
                    color="#2ecc71", linewidth=3.5, zorder=4)

        if limite > 0:
            courant = chemin[limite - 1]
            ax.scatter([positions[courant][0]], [positions[courant][1]],
                       color="#f1c40f", s=180, label="Véhicule de secours", zorder=6)

        ax.scatter([positions[source][0]], [positions[source][1]], color="#e74c3c", s=150, label=f"Départ : {source}", zorder=5)
        ax.scatter([positions[cible][0]], [positions[cible][1]], color="#2ecc71", s=150, label=f"Arrivée : {cible}", zorder=5)

        ax.set_title(f"Intervention en Direct : Étape {limite}/{len(chemin)} | Trajet {source} -> {cible}", color="white", fontsize=12)
        ax.legend(loc="upper right", facecolor="#2c2c34", edgecolor="none", labelcolor="white")
        ax.tick_params(colors="white")

    ani = animation.FuncAnimation(fig, update, frames=len(chemin) + 3, interval=500, repeat=True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    menu_interactif()
