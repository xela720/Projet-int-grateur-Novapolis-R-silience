"""Bonus Visuel : Visualisation et Animation des Algorithmes sur Carte Urbaine.

Conçu pour la démonstration orale de 12 minutes :
- Animation fluide de l'exploration pas à pas de Dijkstra (relaxation et frontière).
- Comparaison graphique avant/après perturbation sur la carte géographique des sites.
- Visualisation de l'arbre couvrant minimal de fibre et de la réparation après panne.
- Sauvegarde autonome en GIF / PNG dans output/ sans aucun impact sur les benchmarks.
"""

import os
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

import heapq
import math
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from src.data_manager import GrapheRoutier, GrapheFibre, FibreArete
from src.shortest_paths import dijkstra, reconstruire_chemin


def animer_dijkstra(
    graphe: GrapheRoutier,
    source: str,
    cible: str,
    fichier_sortie: str = "output/demo_dijkstra.gif",
    fps: int = 3,
):
    """Génère une animation GIF montrant pas à pas l'expansion de Dijkstra sur la carte."""
    os.makedirs(os.path.dirname(fichier_sortie), exist_ok=True)

    # Historique des étapes pour l'animation
    etapes = []
    distances = {s: math.inf for s in graphe.sommets()}
    predecesseurs = {s: None for s in graphe.sommets()}
    visites = set()

    distances[source] = 0.0
    tas = [(0.0, source)]

    while tas:
        d_u, u = heapq.heappop(tas)
        if u in visites:
            continue
        visites.add(u)

        # Enregistre un instantané de l'état
        etapes.append({
            "noeud_courant": u,
            "visites": set(visites),
            "distances": dict(distances),
            "predecesseurs": dict(predecesseurs),
        })

        if u == cible:
            break

        for v, arc in graphe.voisins(u, uniquement_ouverts=True).items():
            if v not in visites:
                w = arc.temps_normal
                if distances[u] + w < distances[v]:
                    distances[v] = distances[u] + w
                    predecesseurs[v] = u
                    heapq.heappush(tas, (distances[v], v))

    # Chemin final
    chemin_final = reconstruire_chemin(predecesseurs, source, cible)

    # Configuration de la figure
    fig, ax = plt.subplots(figsize=(10, 7))

    positions = {s_id: (s.longitude, s.latitude) for s_id, s in graphe.sites.items()}

    def update(frame_idx):
        ax.clear()
        ax.set_facecolor("#1e1e24")
        fig.patch.set_facecolor("#1e1e24")

        # 1. Tracé de toutes les routes (en gris discret)
        for arc in graphe.tous_les_arcs():
            if arc.u in positions and arc.v in positions:
                x1, y1 = positions[arc.u]
                x2, y2 = positions[arc.v]
                ax.plot([x1, x2], [y1, y2], color="#444455", linewidth=1.0, zorder=1)

        # 2. Sommets non visités
        xs = [pos[0] for pos in positions.values()]
        ys = [pos[1] for pos in positions.values()]
        ax.scatter(xs, ys, color="#666677", s=30, zorder=2)

        # Si nous sommes dans les étapes d'exploration
        if frame_idx < len(etapes):
            info = etapes[frame_idx]
            curr = info["noeud_courant"]
            vis = info["visites"]

            # Sommets déjà visités
            vis_x = [positions[s][0] for s in vis if s in positions]
            vis_y = [positions[s][1] for s in vis if s in positions]
            ax.scatter(vis_x, vis_y, color="#3498db", s=70, label="Explorés", zorder=3)

            # Sommet en cours de traitement
            if curr in positions:
                ax.scatter(
                    [positions[curr][0]],
                    [positions[curr][1]],
                    color="#f39c12",
                    s=140,
                    label="Frontière active",
                    zorder=4,
                )

            # Arcs de l'arborescence explorée
            for v_noeud, p_noeud in info["predecesseurs"].items():
                if p_noeud is not None and p_noeud in positions and v_noeud in positions:
                    x1, y1 = positions[p_noeud]
                    x2, y2 = positions[v_noeud]
                    ax.plot([x1, x2], [y1, y2], color="#3498db", linewidth=1.8, zorder=3)

            ax.set_title(
                f"Exploration Dijkstra : Étape {frame_idx + 1}/{len(etapes)} | Nœud en cours : {curr}",
                color="white",
                fontsize=12,
            )
        else:
            # Étape finale : tracé du chemin optimal retenu
            ax.scatter(
                [positions[s][0] for s in positions],
                [positions[s][1] for s in positions],
                color="#3498db",
                s=40,
                zorder=2,
            )
            for i in range(len(chemin_final) - 1):
                u_p = chemin_final[i]
                v_p = chemin_final[i + 1]
                x1, y1 = positions[u_p]
                x2, y2 = positions[v_p]
                ax.plot([x1, x2], [y1, y2], color="#2ecc71", linewidth=3.5, zorder=5)

            # Points origine et destination
            ax.scatter(
                [positions[source][0]],
                [positions[source][1]],
                color="#e74c3c",
                s=160,
                label=f"Départ ({source})",
                zorder=6,
            )
            ax.scatter(
                [positions[cible][0]],
                [positions[cible][1]],
                color="#2ecc71",
                s=160,
                label=f"Arrivée ({cible})",
                zorder=6,
            )

            duree = distances[cible]
            ax.set_title(
                f"Chemin Optimal Trouvé : {len(chemin_final)-1} arcs | Durée : {round(duree, 2)} min",
                color="#2ecc71",
                fontsize=13,
                fontweight="bold",
            )

        ax.legend(loc="upper right", facecolor="#2c2c34", edgecolor="none", labelcolor="white")
        ax.set_xlabel("Longitude", color="white")
        ax.set_ylabel("Latitude", color="white")
        ax.tick_params(colors="white")

    nb_frames = len(etapes) + 4  # Garde l'image finale affichée quelques frames
    ani = animation.FuncAnimation(fig, update, frames=nb_frames, repeat=False)
    ani.save(fichier_sortie, writer="pillow", fps=fps)
    plt.close()
    print(f"-> Animation Dijkstra sauvegardée : {fichier_sortie}")


def visualiser_comparaison_itineraires(
    graphe_base: GrapheRoutier,
    graphe_perturbe: GrapheRoutier,
    chemin_normal: List[str],
    chemin_perturbe: List[str],
    routes_fermees: List[Tuple[str, str]],
    fichier_sortie: str = "output/comparaison_avant_apres.png",
):
    """Crée une vue comparative avant/après montrant la coupure d'axe et la déviation de secours."""
    os.makedirs(os.path.dirname(fichier_sortie), exist_ok=True)
    positions = {s_id: (s.longitude, s.latitude) for s_id, s in graphe_base.sites.items()}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

    for ax, titre, chemin, col_chemin in [
        (ax1, "Situation Normale (Itinéraire Nominal)", chemin_normal, "#2ecc71"),
        (ax2, "Situation Perturbée (Déviation d'Urgence)", chemin_perturbe, "#e67e22"),
    ]:
        ax.set_facecolor("#1e1e24")
        # Fond routier
        for arc in graphe_base.tous_les_arcs():
            if arc.u in positions and arc.v in positions:
                x1, y1 = positions[arc.u]
                x2, y2 = positions[arc.v]
                ax.plot([x1, x2], [y1, y2], color="#444455", linewidth=1.0, zorder=1)

        # Tracé des routes fermées
        for u_f, v_f in routes_fermees:
            if u_f in positions and v_f in positions:
                x1, y1 = positions[u_f]
                x2, y2 = positions[v_f]
                ax.plot([x1, x2], [y1, y2], color="#e74c3c", linewidth=4.0, linestyle="--", label="Axe Coupé", zorder=4)

        # Tracé du chemin retenu
        if chemin:
            for i in range(len(chemin) - 1):
                u_p, v_p = chemin[i], chemin[i + 1]
                x1, y1 = positions[u_p]
                x2, y2 = positions[v_p]
                ax.plot([x1, x2], [y1, y2], color=col_chemin, linewidth=3.5, zorder=5)

            # Balises départ / arrivée
            ax.scatter([positions[chemin[0]][0]], [positions[chemin[0]][1]], color="#e74c3c", s=140, label="Caserne", zorder=6)
            ax.scatter([positions[chemin[-1]][0]], [positions[chemin[-1]][1]], color=col_chemin, s=140, label="Intervention", zorder=6)

        ax.set_title(titre, fontsize=12, color="white", fontweight="bold")
        ax.set_xlabel("Longitude", color="white")
        ax.set_ylabel("Latitude", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="upper right", facecolor="#2c2c34", edgecolor="none", labelcolor="white")

    fig.patch.set_facecolor("#1e1e24")
    plt.tight_layout()
    plt.savefig(fichier_sortie, dpi=300)
    plt.close()
    print(f"-> Comparaison avant/après sauvegardée : {fichier_sortie}")


def visualiser_fibre_et_reparation(
    graphe_fibre: GrapheFibre,
    mst_initial: List[FibreArete],
    panne: Tuple[str, str],
    remplacement: Optional[Tuple[str, str]],
    fichier_sortie: str = "output/reparation_fibre.png",
):
    """Visualise le réseau de fibre, l'arbre couvrant minimal, la panne et le câble de secours."""
    os.makedirs(os.path.dirname(fichier_sortie), exist_ok=True)
    positions = {s_id: (s.longitude, s.latitude) for s_id, s in graphe_fibre.sites.items()}

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_facecolor("#1e1e24")
    fig.patch.set_facecolor("#1e1e24")

    # 1. Toutes les arêtes de fibre potentielles
    for a in graphe_fibre.toutes_les_aretes():
        x1, y1 = positions[a.u]
        x2, y2 = positions[a.v]
        ax.plot([x1, x2], [y1, y2], color="#3d3d4d", linewidth=1.0, zorder=1)

    # 2. Arêtes du MST de base
    paire_panne = tuple(sorted(panne))
    for a in mst_initial:
        if a.extremites() != paire_panne:
            x1, y1 = positions[a.u]
            x2, y2 = positions[a.v]
            ax.plot([x1, x2], [y1, y2], color="#3498db", linewidth=2.5, zorder=2)

    # 3. Arête rompue
    x1, y1 = positions[paire_panne[0]]
    x2, y2 = positions[paire_panne[1]]
    ax.plot([x1, x2], [y1, y2], color="#e74c3c", linewidth=3.5, linestyle="--", label=f"Câble en Panne ({panne[0]}-{panne[1]})", zorder=4)

    # 4. Arête de remplacement
    if remplacement:
        r1, r2 = remplacement
        ax.plot([positions[r1][0], positions[r2][0]], [positions[r1][1], positions[r2][1]], color="#2ecc71", linewidth=3.5, linestyle="-.", label=f"Raccordement Secours ({r1}-{r2})", zorder=5)

    # 5. Sommets
    xs = [pos[0] for pos in positions.values()]
    ys = [pos[1] for pos in positions.values()]
    ax.scatter(xs, ys, color="#f1c40f", s=40, zorder=6, label="Sites raccordés")

    ax.set_title("Résilience Fibre Optique : Arbre Couvrant Minimal & Réparation de Panne", color="white", fontsize=13, fontweight="bold")
    ax.set_xlabel("Longitude", color="white")
    ax.set_ylabel("Latitude", color="white")
    ax.tick_params(colors="white")
    ax.legend(loc="upper right", facecolor="#2c2c34", edgecolor="none", labelcolor="white")

    plt.tight_layout()
    plt.savefig(fichier_sortie, dpi=300)
    plt.close()
    print(f"-> Schéma de réparation fibre sauvegardé : {fichier_sortie}")
