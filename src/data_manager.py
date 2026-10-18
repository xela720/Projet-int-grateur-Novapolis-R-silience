"""Module de gestion des données et des graphes pour Novapolis Résilience.

Ce module prend en charge :
- La modélisation orientée objet des sites, routes, fibres, demandes et scénarios.
- La structure de graphe orienté pondéré pour le réseau routier.
- La structure de graphe non orienté pondéré pour le réseau de fibre optique.
- La validation stricte des fichiers CSV (unicité des identifiants, rejet des références inconnues).
- Le clonage profond des graphes pour garantir que les scénarios ne modifient jamais les données de base.
"""

import os
import csv
import copy
from typing import Dict, List, Tuple, Set, Optional, Any


class Site:
    """Représente un site urbain (caserne, hôpital, école, quartier, télécom, etc.)."""

    def __init__(self, site_id: str, nom: str, type_site: str, longitude: float, latitude: float):
        self.id = str(site_id).strip()
        self.nom = str(nom).strip()
        self.type = str(type_site).strip()
        self.longitude = float(longitude)
        self.latitude = float(latitude)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nom": self.nom,
            "type": self.type,
            "longitude": self.longitude,
            "latitude": self.latitude,
        }

    def __repr__(self) -> str:
        return f"Site(id={self.id!r}, nom={self.nom!r}, type={self.type!r})"


class RouteArc:
    """Représente un arc orienté du réseau routier."""

    def __init__(
        self,
        u: str,
        v: str,
        temps_normal: float,
        temps_pointe: float,
        statut: str = "ouvert",
        type_voie: str = "rue_locale",
        capacite: int = 800,
    ):
        self.u = str(u).strip()
        self.v = str(v).strip()
        self.temps_normal = float(temps_normal)
        self.temps_pointe = float(temps_pointe)
        self.statut = str(statut).strip().lower()
        self.type_voie = str(type_voie).strip()
        self.capacite = int(capacite)

    def est_ouvert(self) -> bool:
        return self.statut == "ouvert"

    def get_poids(self, mode: str = "temps_normal") -> float:
        if mode == "temps_pointe":
            return self.temps_pointe
        return self.temps_normal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "u": self.u,
            "v": self.v,
            "temps_normal": self.temps_normal,
            "temps_pointe": self.temps_pointe,
            "statut": self.statut,
            "type_voie": self.type_voie,
            "capacite": self.capacite,
        }

    def __repr__(self) -> str:
        return (
            f"RouteArc({self.u}->{self.v}, normal={self.temps_normal}, "
            f"pointe={self.temps_pointe}, statut={self.statut})"
        )


class FibreArete:
    """Représente une arête non orientée du réseau de fibre optique."""

    def __init__(self, u: str, v: str, cost: float, statut: str = "actif"):
        self.u = str(u).strip()
        self.v = str(v).strip()
        self.cost = float(cost)
        self.statut = str(statut).strip().lower()

    def est_actif(self) -> bool:
        return self.statut == "actif"

    def extremites(self) -> Tuple[str, str]:
        return tuple(sorted([self.u, self.v]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "u": self.u,
            "v": self.v,
            "cost": self.cost,
            "statut": self.statut,
        }

    def __repr__(self) -> str:
        return f"FibreArete({self.u}--{self.v}, cost={self.cost}, statut={self.statut})"


class Demande:
    """Représente une demande de secours ou d'intervention."""

    def __init__(self, demande_id: str, origine: str, destination: str, type_demande: str, priorite: int = 1):
        self.id = str(demande_id).strip()
        self.origine = str(origine).strip()
        self.destination = str(destination).strip()
        self.type = str(type_demande).strip()
        self.priorite = int(priorite)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "origine": self.origine,
            "destination": self.destination,
            "type": self.type,
            "priorite": self.priorite,
        }

    def __repr__(self) -> str:
        return f"Demande({self.id}, {self.origine}->{self.destination}, prio={self.priorite})"


class ScenarioAction:
    """Représente une perturbation ou modification appliquée dans un scénario."""

    def __init__(self, scenario_id: str, type_element: str, u: str, v: str, action: str, valeur: float = 0.0):
        self.scenario_id = str(scenario_id).strip()
        self.type_element = str(type_element).strip().lower()
        self.u = str(u).strip()
        self.v = str(v).strip()
        self.action = str(action).strip().lower()
        self.valeur = float(valeur)

    def __repr__(self) -> str:
        return f"ScenarioAction({self.scenario_id}: {self.type_element} {self.u}-{self.v} {self.action} {self.valeur})"


class GrapheRoutier:
    """Graphe orienté représentant le réseau routier."""

    def __init__(self):
        self.sites: Dict[str, Site] = {}
        # Adjacence sortante : u -> {v: RouteArc}
        self.adj: Dict[str, Dict[str, RouteArc]] = {}
        # Adjacence entrante : v -> {u: RouteArc} (utile pour analyse connexité)
        self.adj_inv: Dict[str, Dict[str, RouteArc]] = {}

    def ajouter_site(self, site: Site):
        if site.id in self.sites:
            raise ValueError(f"Site en doublon détecté : {site.id}")
        self.sites[site.id] = site
        self.adj[site.id] = {}
        self.adj_inv[site.id] = {}

    def ajouter_arc(self, arc: RouteArc):
        if arc.u not in self.sites:
            raise KeyError(f"Site origine inexistant pour la route : {arc.u}")
        if arc.v not in self.sites:
            raise KeyError(f"Site destination inexistant pour la route : {arc.v}")
        self.adj[arc.u][arc.v] = arc
        self.adj_inv[arc.v][arc.u] = arc

    def sommets(self) -> List[str]:
        return list(self.sites.keys())

    def voisins(self, u: str, uniquement_ouverts: bool = True) -> Dict[str, RouteArc]:
        if u not in self.adj:
            raise KeyError(f"Sommet inconnu : {u}")
        if not uniquement_ouverts:
            return self.adj[u].copy()
        return {v: arc for v, arc in self.adj[u].items() if arc.est_ouvert()}

    def voisins_entrants(self, v: str, uniquement_ouverts: bool = True) -> Dict[str, RouteArc]:
        if v not in self.adj_inv:
            raise KeyError(f"Sommet inconnu : {v}")
        if not uniquement_ouverts:
            return self.adj_inv[v].copy()
        return {u: arc for u, arc in self.adj_inv[v].items() if arc.est_ouvert()}

    def tous_les_arcs(self, uniquement_ouverts: bool = False) -> List[RouteArc]:
        arcs = []
        for u in self.adj:
            for v, arc in self.adj[u].items():
                if not uniquement_ouverts or arc.est_ouvert():
                    arcs.append(arc)
        return arcs

    def cloner(self) -> "GrapheRoutier":
        """Effectue une copie indépendante profonde du graphe."""
        nouveau = GrapheRoutier()
        for site_id, site in self.sites.items():
            nouveau.sites[site_id] = Site(site.id, site.nom, site.type, site.longitude, site.latitude)
            nouveau.adj[site_id] = {}
            nouveau.adj_inv[site_id] = {}
        for arc in self.tous_les_arcs(uniquement_ouverts=False):
            nouveau_arc = RouteArc(
                arc.u,
                arc.v,
                arc.temps_normal,
                arc.temps_pointe,
                arc.statut,
                arc.type_voie,
                arc.capacite,
            )
            nouveau.ajouter_arc(nouveau_arc)
        return nouveau


class GrapheFibre:
    """Graphe non orienté représentant le réseau de fibre optique."""

    def __init__(self):
        self.sites: Dict[str, Site] = {}
        # Adjacence symétrique : u -> {v: FibreArete}
        self.adj: Dict[str, Dict[str, FibreArete]] = {}
        self.aretes_uniques: Dict[Tuple[str, str], FibreArete] = {}

    def ajouter_site(self, site: Site):
        if site.id in self.sites:
            raise ValueError(f"Site en doublon détecté : {site.id}")
        self.sites[site.id] = site
        self.adj[site.id] = {}

    def ajouter_arete(self, arete: FibreArete):
        if arete.u not in self.sites:
            raise KeyError(f"Site origine inexistant pour la fibre : {arete.u}")
        if arete.v not in self.sites:
            raise KeyError(f"Site destination inexistant pour la fibre : {arete.v}")
        paire = arete.extremites()
        self.aretes_uniques[paire] = arete
        self.adj[arete.u][arete.v] = arete
        self.adj[arete.v][arete.u] = arete

    def sommets(self) -> List[str]:
        return list(self.sites.keys())

    def voisins(self, u: str, uniquement_actifs: bool = True) -> Dict[str, FibreArete]:
        if u not in self.adj:
            raise KeyError(f"Sommet inconnu : {u}")
        if not uniquement_actifs:
            return self.adj[u].copy()
        return {v: arete for v, arete in self.adj[u].items() if arete.est_actif()}

    def toutes_les_aretes(self, uniquement_actifs: bool = False) -> List[FibreArete]:
        if not uniquement_actifs:
            return list(self.aretes_uniques.values())
        return [arete for arete in self.aretes_uniques.values() if arete.est_actif()]

    def cloner(self) -> "GrapheFibre":
        """Effectue une copie indépendante profonde du graphe fibre."""
        nouveau = GrapheFibre()
        for site_id, site in self.sites.items():
            nouveau.sites[site_id] = Site(site.id, site.nom, site.type, site.longitude, site.latitude)
            nouveau.adj[site_id] = {}
        for arete in self.toutes_les_aretes(uniquement_actifs=False):
            nouvelle_arete = FibreArete(arete.u, arete.v, arete.cost, arete.statut)
            nouveau.ajouter_arete(nouvelle_arete)
        return nouveau


class ReseauNovapolis:
    """Conteneur principal regroupant les deux graphes et les données associées."""

    def __init__(
        self,
        graphe_routier: GrapheRoutier,
        graphe_fibre: GrapheFibre,
        demandes: List[Demande],
        scenarios: Dict[str, List[ScenarioAction]],
    ):
        self.routier = graphe_routier
        self.fibre = graphe_fibre
        self.demandes = demandes
        self.scenarios = scenarios

    def cloner(self) -> "ReseauNovapolis":
        return ReseauNovapolis(
            self.routier.cloner(),
            self.fibre.cloner(),
            copy.deepcopy(self.demandes),
            copy.deepcopy(self.scenarios),
        )


def charger_reseau(dossier_data: str) -> ReseauNovapolis:
    """Charge et valide rigoureusement l'ensemble des fichiers CSV d'un dossier.

    Règles de validation :
    - Rejet immédiat avec message explicite de tout ID de site en doublon.
    - Rejet immédiat de toute route ou fibre faisant référence à un site non répertorié.
    - Vérification du type numérique des coûts, temps et coordonnées.
    """
    fichier_sites = os.path.join(dossier_data, "sites.csv")
    fichier_routes = os.path.join(dossier_data, "routes.csv")
    fichier_fibre = os.path.join(dossier_data, "fibre.csv")
    fichier_demandes = os.path.join(dossier_data, "demandes.csv")
    fichier_scenarios = os.path.join(dossier_data, "scenarios.csv")

    for chemin in [fichier_sites, fichier_routes, fichier_fibre]:
        if not os.path.exists(chemin):
            raise FileNotFoundError(f"Fichier obligatoire manquant : {chemin}")

    # 1. Chargement des sites
    graphe_routier = GrapheRoutier()
    graphe_fibre = GrapheFibre()
    sites_vus = set()

    with open(fichier_sites, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for num_ligne, row in enumerate(reader, start=2):
            s_id = row["id"].strip()
            if not s_id:
                raise ValueError(f"Ligne {num_ligne} de sites.csv : l'identifiant ne peut être vide.")
            if s_id in sites_vus:
                raise ValueError(f"Erreur de validation : Identifiant de site en doublon '{s_id}' à la ligne {num_ligne}.")
            sites_vus.add(s_id)

            try:
                lon = float(row["longitude"])
                lat = float(row["latitude"])
            except ValueError:
                raise ValueError(f"Ligne {num_ligne} de sites.csv : coordonnées invalides pour le site '{s_id}'.")

            site = Site(s_id, row["nom"], row["type"], lon, lat)
            graphe_routier.ajouter_site(site)
            graphe_fibre.ajouter_site(Site(s_id, row["nom"], row["type"], lon, lat))

    # 2. Chargement des routes
    routes_vues = set()
    with open(fichier_routes, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for num_ligne, row in enumerate(reader, start=2):
            u = row["u"].strip()
            v = row["v"].strip()
            if u not in sites_vus:
                raise KeyError(
                    f"Erreur de validation routes.csv ligne {num_ligne} : "
                    f"le site d'origine '{u}' n'existe pas dans sites.csv."
                )
            if v not in sites_vus:
                raise KeyError(
                    f"Erreur de validation routes.csv ligne {num_ligne} : "
                    f"le site de destination '{v}' n'existe pas dans sites.csv."
                )

            if (u, v) in routes_vues:
                raise ValueError(f"Erreur routes.csv ligne {num_ligne} : arc doublon ({u}->{v}).")
            routes_vues.add((u, v))

            try:
                t_norm = float(row["temps_normal"])
                t_pte = float(row["temps_pointe"])
            except ValueError:
                raise ValueError(f"Ligne {num_ligne} de routes.csv : temps non numériques pour {u}->{v}.")

            statut = row.get("statut", "ouvert").strip().lower()
            type_voie = row.get("type_voie", "rue_locale")
            capacite = int(row.get("capacite", 800))

            arc = RouteArc(u, v, t_norm, t_pte, statut, type_voie, capacite)
            graphe_routier.ajouter_arc(arc)

    # 3. Chargement de la fibre
    fibres_vues = set()
    with open(fichier_fibre, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for num_ligne, row in enumerate(reader, start=2):
            u = row["u"].strip()
            v = row["v"].strip()
            if u not in sites_vus:
                raise KeyError(
                    f"Erreur de validation fibre.csv ligne {num_ligne} : "
                    f"le site d'extrémité '{u}' n'existe pas dans sites.csv."
                )
            if v not in sites_vus:
                raise KeyError(
                    f"Erreur de validation fibre.csv ligne {num_ligne} : "
                    f"le site d'extrémité '{v}' n'existe pas dans sites.csv."
                )

            paire = tuple(sorted([u, v]))
            if paire in fibres_vues:
                raise ValueError(f"Erreur fibre.csv ligne {num_ligne} : arête doublon ({u}--{v}).")
            fibres_vues.add(paire)

            try:
                cost = float(row["cost"])
            except ValueError:
                raise ValueError(f"Ligne {num_ligne} de fibre.csv : coût non numérique pour {u}--{v}.")

            statut = row.get("statut", "actif").strip().lower()
            arete = FibreArete(u, v, cost, statut)
            graphe_fibre.ajouter_arete(arete)

    # 4. Chargement des demandes (si présent)
    demandes: List[Demande] = []
    if os.path.exists(fichier_demandes):
        with open(fichier_demandes, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            demandes_vues = set()
            for num_ligne, row in enumerate(reader, start=2):
                d_id = row["id"].strip()
                if d_id in demandes_vues:
                    raise ValueError(f"Erreur demandes.csv ligne {num_ligne} : identifiant en doublon '{d_id}'.")
                demandes_vues.add(d_id)

                origine = row["origine"].strip()
                if origine not in sites_vus:
                    raise KeyError(f"Erreur demandes.csv ligne {num_ligne} : site origine '{origine}' inconnu.")

                # Gère la colonne optionnelle 'destination'
                destination = row.get("destination", "").strip()
                if destination and destination not in sites_vus:
                    raise KeyError(f"Erreur demandes.csv ligne {num_ligne} : site destination '{destination}' inconnu.")

                d_type = row.get("type", "urgence").strip()
                prio = int(row.get("priorite", 1))
                demandes.append(Demande(d_id, origine, destination, d_type, prio))

    # 5. Chargement des scénarios (si présent)
    scenarios: Dict[str, List[ScenarioAction]] = {}
    if os.path.exists(fichier_scenarios):
        with open(fichier_scenarios, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for num_ligne, row in enumerate(reader, start=2):
                sc_id = row["scenario_id"].strip()
                t_elem = row["type_element"].strip().lower()
                u = row["u"].strip()
                v = row["v"].strip()
                action = row["action"].strip().lower()
                valeur = float(row.get("valeur", 0.0))

                if sc_id not in scenarios:
                    scenarios[sc_id] = []

                if action != "baseline" and t_elem != "aucun":
                    if u not in sites_vus:
                        raise KeyError(f"Scénario '{sc_id}' ligne {num_ligne} : sommet '{u}' inconnu.")
                    if v not in sites_vus:
                        raise KeyError(f"Scénario '{sc_id}' ligne {num_ligne} : sommet '{v}' inconnu.")

                scenarios[sc_id].append(ScenarioAction(sc_id, t_elem, u, v, action, valeur))

    return ReseauNovapolis(graphe_routier, graphe_fibre, demandes, scenarios)


def appliquer_scenario(
    reseau_base: ReseauNovapolis, scenario_id: str
) -> ReseauNovapolis:
    """Applique un scénario sur une copie indépendante du réseau sans modifier la base."""
    reseau_perturbe = reseau_base.cloner()

    if scenario_id not in reseau_base.scenarios or scenario_id == "scenario_normal":
        return reseau_perturbe

    actions = reseau_base.scenarios[scenario_id]
    for act in actions:
        if act.type_element == "route":
            # Perturbation sur le réseau routier
            if act.u in reseau_perturbe.routier.adj and act.v in reseau_perturbe.routier.adj[act.u]:
                arc = reseau_perturbe.routier.adj[act.u][act.v]
                if act.action in ("fermer", "bloquer", "desactiver"):
                    arc.statut = "ferme"
                elif act.action == "ouvrir":
                    arc.statut = "ouvert"
                elif act.action == "modifier_temps":
                    arc.temps_normal *= act.valeur
                    arc.temps_pointe *= act.valeur
                elif act.action == "supprimer":
                    del reseau_perturbe.routier.adj[act.u][act.v]
                    if act.u in reseau_perturbe.routier.adj_inv[act.v]:
                        del reseau_perturbe.routier.adj_inv[act.v][act.u]

        elif act.type_element == "fibre":
            # Perturbation sur le réseau fibre (non orienté)
            paire = tuple(sorted([act.u, act.v]))
            if paire in reseau_perturbe.fibre.aretes_uniques:
                arete = reseau_perturbe.fibre.aretes_uniques[paire]
                if act.action in ("fermer", "panne", "desactiver"):
                    arete.statut = "inactif"
                elif act.action == "ouvrir":
                    arete.statut = "actif"
                elif act.action == "supprimer":
                    del reseau_perturbe.fibre.aretes_uniques[paire]
                    if act.v in reseau_perturbe.fibre.adj[act.u]:
                        del reseau_perturbe.fibre.adj[act.u][act.v]
                    if act.u in reseau_perturbe.fibre.adj[act.v]:
                        del reseau_perturbe.fibre.adj[act.v][act.u]

    return reseau_perturbe
