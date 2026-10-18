"""Un graphe pondéré non orienté pour préparer Dijkstra et A*.

Les sommets ont un nom et des coordonnées cartésiennes (x, y).
Chaque arête représente une route à double sens avec un coût positif ou nul.
Les coordonnées servent au dessin ; les poids définissent le coût du trajet.
Pour A*, une distance géométrique ne sera une heuristique valable que si elle
ne surestime jamais le coût restant, avec des unités compatibles.
"""

from math import isfinite
from numbers import Real


def _verifier_nombre(valeur, nom):
    if isinstance(valeur, bool) or not isinstance(valeur, Real):
        raise TypeError(f"{nom} doit être un nombre réel.")
    if not isfinite(valeur):
        raise ValueError(f"{nom} doit être fini.")


class Graphe:
    """Stocke les positions et les voisins de chaque sommet."""

    def __init__(self):
        self._positions = {}
        self._adjacence = {}

    def ajouter_sommet(self, nom, x, y):
        """Ajoute un sommet isolé. Un nom existant est refusé."""
        if not isinstance(nom, str):
            raise TypeError("Le nom du sommet doit être une chaîne de caractères.")
        if not nom.strip():
            raise ValueError("Le nom du sommet ne doit pas être vide.")
        if nom in self._positions:
            raise ValueError(f"Le sommet {nom!r} existe déjà.")
        _verifier_nombre(x, "x")
        _verifier_nombre(y, "y")

        self._positions[nom] = (x, y)
        self._adjacence[nom] = {}

    def ajouter_arete(self, depart, arrivee, poids):
        """Ajoute une route à double sens ou remplace son poids si elle existe."""
        if depart not in self._adjacence:
            raise KeyError(f"Sommet inconnu : {depart!r}.")
        if arrivee not in self._adjacence:
            raise KeyError(f"Sommet inconnu : {arrivee!r}.")
        _verifier_nombre(poids, "Le poids")
        if poids < 0:
            raise ValueError("Le poids doit être positif ou nul.")

        self._adjacence[depart][arrivee] = poids
        self._adjacence[arrivee][depart] = poids

    def sommets(self):
        """Renvoie la liste des noms des sommets."""
        return list(self._adjacence)

    def positions(self):
        """Renvoie une copie des coordonnées, utile pour dessiner le graphe."""
        return self._positions.copy()

    def voisins(self, sommet):
        """Renvoie une copie du dictionnaire {voisin: poids}."""
        return self._adjacence[sommet].copy()

    def aretes(self):
        """Renvoie chaque route une seule fois sous la forme (départ, arrivée, poids)."""
        resultat = []
        sommets_vus = set()
        for depart, voisins in self._adjacence.items():
            for arrivee, poids in voisins.items():
                if arrivee not in sommets_vus:
                    resultat.append((depart, arrivee, poids))
            sommets_vus.add(depart)
        return resultat


def creer_exemple():
    """Crée cinq sommets. Le trajet minimal de A à E est A-C-D-E, de coût 6."""
    graphe = Graphe()
    for nom, x, y in [
        ("A", 0, 0),
        ("B", 2, 0),
        ("C", 0, 2),
        ("D", 2, 2),
        ("E", 4, 2),
    ]:
        graphe.ajouter_sommet(nom, x, y)

    for depart, arrivee, poids in [
        ("A", "B", 2),
        ("A", "C", 2),
        ("B", "D", 3),
        ("C", "D", 2),
        ("B", "E", 6),
        ("D", "E", 2),
    ]:
        graphe.ajouter_arete(depart, arrivee, poids)
    return graphe


if __name__ == "__main__":
    exemple = creer_exemple()
    print("Sommets :", exemple.sommets())
    print("Routes :", exemple.aretes())
    print("Voisins de A :", exemple.voisins("A"))
