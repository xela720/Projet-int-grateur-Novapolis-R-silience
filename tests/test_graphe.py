import unittest

from src.graphe import Graphe, creer_exemple


class TestGraphe(unittest.TestCase):
    def setUp(self):
        self.graphe = Graphe()
        self.graphe.ajouter_sommet("A", 0, 0)
        self.graphe.ajouter_sommet("B", 2, 0)

    def test_graphe_vide(self):
        graphe = Graphe()
        self.assertEqual(graphe.sommets(), [])
        self.assertEqual(graphe.positions(), {})
        self.assertEqual(graphe.aretes(), [])

    def test_ajouter_sommet(self):
        self.graphe.ajouter_sommet("C", -1.5, 3)
        self.assertEqual(self.graphe.sommets(), ["A", "B", "C"])
        self.assertEqual(self.graphe.positions()["C"], (-1.5, 3))
        self.assertEqual(self.graphe.voisins("C"), {})

    def test_nom_invalide_ou_deja_present(self):
        positions = self.graphe.positions()
        for nom, erreur in [(1, TypeError), (None, TypeError),
                            (True, TypeError), ("", ValueError),
                            ("  ", ValueError), ("A", ValueError)]:
            with self.subTest(nom=nom):
                with self.assertRaises(erreur):
                    self.graphe.ajouter_sommet(nom, 9, 9)
                self.assertEqual(self.graphe.positions(), positions)
                self.assertEqual(self.graphe.sommets(), ["A", "B"])

    def test_coordonnees_invalides(self):
        valeurs = [(True, TypeError), ("2", TypeError), (None, TypeError),
                   (float("nan"), ValueError), (float("inf"), ValueError),
                   (-float("inf"), ValueError)]
        for valeur, erreur in valeurs:
            for x, y in [(valeur, 0), (0, valeur)]:
                with self.subTest(x=x, y=y):
                    with self.assertRaises(erreur):
                        self.graphe.ajouter_sommet("C", x, y)
                    self.assertEqual(self.graphe.sommets(), ["A", "B"])
                    self.assertNotIn("C", self.graphe.positions())

    def test_arete_non_orientee_et_poids_nul(self):
        self.graphe.ajouter_arete("A", "B", 0)
        self.assertEqual(self.graphe.voisins("A"), {"B": 0})
        self.assertEqual(self.graphe.voisins("B"), {"A": 0})
        self.assertEqual(len(self.graphe.aretes()), 1)

    def test_sommets_absents(self):
        self.graphe.ajouter_arete("A", "B", 2)
        for depart, arrivee in [("A", "X"), ("X", "A"), ("X", "Y")]:
            with self.subTest(depart=depart, arrivee=arrivee):
                with self.assertRaises(KeyError):
                    self.graphe.ajouter_arete(depart, arrivee, 1)
                self.assertEqual(self.graphe.voisins("A"), {"B": 2})
                self.assertEqual(self.graphe.voisins("B"), {"A": 2})
                self.assertEqual(self.graphe.sommets(), ["A", "B"])
        with self.assertRaises(KeyError):
            self.graphe.voisins("X")

    def test_poids_invalide_ne_modifie_pas_arete(self):
        self.graphe.ajouter_arete("A", "B", 2)
        valeurs = [(-1, ValueError), (float("nan"), ValueError),
                   (float("inf"), ValueError), (-float("inf"), ValueError),
                   (True, TypeError), ("2", TypeError), (None, TypeError)]
        for poids, erreur in valeurs:
            with self.subTest(poids=poids):
                with self.assertRaises(erreur):
                    self.graphe.ajouter_arete("A", "B", poids)
                self.assertEqual(self.graphe.voisins("A"), {"B": 2})
                self.assertEqual(self.graphe.voisins("B"), {"A": 2})

    def test_mise_a_jour_arete_dans_les_deux_sens(self):
        self.graphe.ajouter_arete("A", "B", 2)
        self.graphe.ajouter_arete("B", "A", 1.5)
        self.assertEqual(self.graphe.voisins("A"), {"B": 1.5})
        self.assertEqual(self.graphe.voisins("B"), {"A": 1.5})
        self.assertEqual(len(self.graphe.aretes()), 1)

    def test_boucle_presente_une_seule_fois(self):
        self.graphe.ajouter_arete("A", "A", 0)
        self.assertEqual(self.graphe.voisins("A"), {"A": 0})
        self.assertEqual(self.graphe.aretes(), [("A", "A", 0)])

    def test_copies_ne_modifient_pas_le_graphe(self):
        self.graphe.ajouter_arete("A", "B", 2)
        self.graphe.sommets().clear()
        self.graphe.positions()["A"] = (99, 99)
        self.graphe.voisins("A")["B"] = -1
        self.graphe.aretes().clear()
        self.assertEqual(self.graphe.sommets(), ["A", "B"])
        self.assertEqual(self.graphe.positions(), {"A": (0, 0), "B": (2, 0)})
        self.assertEqual(self.graphe.voisins("A"), {"B": 2})
        self.assertEqual(self.graphe.voisins("B"), {"A": 2})
        self.assertEqual(len(self.graphe.aretes()), 1)

    def test_exemple(self):
        graphe = creer_exemple()
        self.assertEqual(graphe.positions(), {
            "A": (0, 0), "B": (2, 0), "C": (0, 2),
            "D": (2, 2), "E": (4, 2),
        })
        attendues = {("A", "B"): 2, ("A", "C"): 2, ("B", "D"): 3,
                     ("C", "D"): 2, ("B", "E"): 6, ("D", "E"): 2}
        aretes = graphe.aretes()
        self.assertEqual(len(aretes), len(attendues))
        self.assertEqual({tuple(sorted((a, b))): poids for a, b, poids in aretes},
                         attendues)
        for (a, b), poids in attendues.items():
            self.assertEqual(graphe.voisins(a)[b], poids)
            self.assertEqual(graphe.voisins(b)[a], poids)


if __name__ == "__main__":
    unittest.main()
