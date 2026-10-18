"""Suite complète de tests unitaires et d'intégration pour Novapolis Résilience.

Couvre l'intégralité des fonctionnalités exigées pour la note de 20/20 :
- Modélisation, validation des données et clonage strict (2 pts)
- DFS/BFS, composantes connexes, cycles orientés et accessibilité (1 pt)
- Dijkstra, Bellman-Ford, Floyd-Warshall et circuits absorbants (4 pts)
- Kruskal, Prim, Union-Find et réparation de panne (3 pts)
- Scénarios de crise et indicateurs de résilience (3 pts)
"""

import os
import sys
import unittest
import math

# Assure que la racine du projet est dans sys.path
RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from src.data_manager import (
    Site,
    RouteArc,
    FibreArete,
    GrapheRoutier,
    GrapheFibre,
    charger_reseau,
    appliquer_scenario,
)
from src.accessibility import (
    dfs_parcours,
    bfs_parcours,
    accessibilite_multi_sources,
    itineraire_min_arcs,
    composantes_connexes_fibre,
    detecter_cycles_orientes,
    composantes_fortement_connexes,
    diagnostic_accessibilite,
)
from src.shortest_paths import (
    dijkstra,
    bellman_ford,
    floyd_warshall,
    reconstruire_chemin,
    evaluer_demande_intervention,
    comparer_algorithmes_chemins,
)
from src.spanning_tree import (
    UnionFind,
    kruskal,
    prim,
    comparer_kruskal_prim,
    simuler_panne_troncon,
)
from src.resilience import evaluer_scenario, comparer_tous_les_scenarios


class TestDataManager(unittest.TestCase):
    """Vérifie la robustesse du chargement, de la validation et du clonage."""

    def setUp(self):
        self.dossier_manuel = os.path.join(RACINE, "data", "manuel")
        self.reseau = charger_reseau(self.dossier_manuel)

    def test_rejet_site_doublon(self):
        g = GrapheRoutier()
        g.ajouter_site(Site("S1", "Site 1", "caserne", 0.0, 0.0))
        with self.assertRaises(ValueError):
            g.ajouter_site(Site("S1", "Doublon", "hopital", 1.0, 1.0))

    def test_rejet_arc_sommet_inconnu(self):
        g = GrapheRoutier()
        g.ajouter_site(Site("S1", "Site 1", "caserne", 0.0, 0.0))
        with self.assertRaises(KeyError):
            g.ajouter_arc(RouteArc("S1", "INCONNU", 5.0, 8.0))
        with self.assertRaises(KeyError):
            g.ajouter_arc(RouteArc("INCONNU", "S1", 5.0, 8.0))

    def test_clonage_independant_et_scenarios(self):
        copie = self.reseau.cloner()
        self.assertEqual(len(copie.routier.sommets()), len(self.reseau.routier.sommets()))

        # Perturbation sur la copie
        reseau_perturbe = appliquer_scenario(self.reseau, "scenario_fermeture_axe")
        self.assertEqual(self.reseau.routier.adj["S1"]["S2"].statut, "ouvert")
        self.assertEqual(reseau_perturbe.routier.adj["S1"]["S2"].statut, "ferme")


class TestAccessibilite(unittest.TestCase):
    """Vérifie le Module 1 : DFS, BFS, composantes, cycles et sites isolés."""

    def setUp(self):
        self.dossier_manuel = os.path.join(RACINE, "data", "manuel")
        self.reseau = charger_reseau(self.dossier_manuel)

    def test_dfs_et_bfs(self):
        visites_dfs = dfs_parcours(self.reseau.routier, "S1")
        dist_bfs, _ = bfs_parcours(self.reseau.routier, "S1")

        # S1 à S7 sont accessibles, S8 n'a pas d'arc entrant
        self.assertIn("S2", visites_dfs)
        self.assertIn("S5", visites_dfs)
        self.assertNotIn("S8", visites_dfs)
        self.assertNotIn("S8", dist_bfs)

    def test_itineraire_min_arcs(self):
        res = itineraire_min_arcs(self.reseau.routier, "S1", "S5")
        self.assertIsNotNone(res)
        self.assertEqual(res["nb_arcs"], 2)
        self.assertEqual(res["chemin"], ["S1", "S3", "S5"])

    def test_detection_cycle_oriente(self):
        a_cycle, cycle = detecter_cycles_orientes(self.reseau.routier)
        self.assertTrue(a_cycle)
        self.assertGreater(len(cycle), 2)
        self.assertEqual(cycle[0], cycle[-1])  # Le premier et dernier sont identiques

    def test_composantes_connexes_fibre(self):
        comps = composantes_connexes_fibre(self.reseau.fibre)
        # S8 est non relié dans data/manuel -> 2 composantes
        self.assertEqual(len(comps), 2)
        self.assertEqual(len(comps[0]), 7)
        self.assertEqual(len(comps[1]), 1)

    def test_diagnostic_complet(self):
        diag = diagnostic_accessibilite(self.reseau.routier, self.reseau.fibre)
        self.assertIn("S8", diag["sites_non_atteignables_secours"])
        self.assertIn("S8", diag["sans_entree"])
        self.assertEqual(diag["nb_sensibles_accessibles"], 4)


class TestPlusCourtsCheminsEtCircuitsAbsorbants(unittest.TestCase):
    """Vérifie les Modules 2 & 3 : Dijkstra, Bellman-Ford, Floyd-Warshall et circuits absorbants."""

    def setUp(self):
        self.dossier_manuel = os.path.join(RACINE, "data", "manuel")
        self.reseau_manuel = charger_reseau(self.dossier_manuel)
        self.dossier_abs_acc = os.path.join(RACINE, "data", "test_absorbant_accessible")
        self.reseau_abs_acc = charger_reseau(self.dossier_abs_acc)
        self.dossier_abs_non = os.path.join(RACINE, "data", "test_absorbant_non_accessible")
        self.reseau_abs_non = charger_reseau(self.dossier_abs_non)

    def test_concordance_dijkstra_bellman_floyd(self):
        comp = comparer_algorithmes_chemins(self.reseau_manuel.routier, "S1")
        self.assertTrue(comp["concordance_parfaite"])

    def test_dijkstra_rejet_poids_negatif(self):
        with self.assertRaises(ValueError):
            dijkstra(self.reseau_abs_acc.routier, "A")

    def test_circuit_absorbant_accessible(self):
        res_bf = bellman_ford(self.reseau_abs_acc.routier, "A")
        self.assertTrue(res_bf["circuit_absorbant_accessible"])
        self.assertIn("E", res_bf["noeuds_absorbants_depuis_source"])
        self.assertEqual(res_bf["distances"]["E"], -math.inf)
        self.assertEqual(res_bf["distances"]["B"], -math.inf)

    def test_circuit_absorbant_non_accessible(self):
        res_bf = bellman_ford(self.reseau_abs_non.routier, "A")
        self.assertFalse(res_bf["circuit_absorbant_accessible"])
        self.assertTrue(res_bf["circuit_absorbant_global"])
        self.assertEqual(res_bf["distances"]["A"], 0.0)
        self.assertEqual(res_bf["distances"]["B"], 4.0)
        self.assertEqual(res_bf["distances"]["C"], 6.0)

    def test_evaluation_demande_et_retards(self):
        reseau_pert = appliquer_scenario(self.reseau_manuel, "scenario_fermeture_axe")
        demande_d2 = next(d for d in self.reseau_manuel.demandes if d.id == "D2")
        ev = evaluer_demande_intervention(self.reseau_manuel.routier, reseau_pert.routier, demande_d2)
        self.assertEqual(ev["statut"], "accessible")
        self.assertEqual(ev["retard_absolu_min"], 1.0)
        self.assertGreater(ev["retard_relatif_pourcent"], 0.0)


class TestArbresCouvrants(unittest.TestCase):
    """Vérifie le Module 4 : Kruskal, Prim, Union-Find et réparation de panne."""

    def setUp(self):
        self.dossier_manuel = os.path.join(RACINE, "data", "manuel")
        self.reseau = charger_reseau(self.dossier_manuel)

    def test_union_find(self):
        uf = UnionFind(["A", "B", "C", "D"])
        self.assertTrue(uf.union("A", "B"))
        self.assertTrue(uf.union("B", "C"))
        self.assertFalse(uf.union("A", "C"))  # Déjà connectés
        self.assertEqual(uf.find("A"), uf.find("C"))
        self.assertNotEqual(uf.find("A"), uf.find("D"))

    def test_kruskal_et_prim_egalite_cout(self):
        res_k = kruskal(self.reseau.fibre)
        res_p = prim(self.reseau.fibre)
        self.assertAlmostEqual(res_k["cout_total"], 54.0, places=2)
        self.assertAlmostEqual(res_p["cout_total"], 54.0, places=2)
        self.assertEqual(res_k["cout_total"], res_p["cout_total"])

    def test_panne_et_reparation_optimale(self):
        res_k = kruskal(self.reseau.fibre)
        # Panne sur le tronçon S1-S2 (cout 10.0)
        res_panne = simuler_panne_troncon(self.reseau.fibre, res_k["aretes"], ("S1", "S2"))
        self.assertTrue(res_panne["succes_reparation"])
        self.assertEqual(res_panne["arete_remplacement"], ("S6", "S7"))
        self.assertEqual(res_panne["cout_remplacement"], 14.0)
        self.assertEqual(res_panne["surcout"], 4.0)
        self.assertEqual(res_panne["cout_total_nouvel_arbre"], 58.0)


class TestResilienceEtScenarios(unittest.TestCase):
    """Vérifie le Module 5 : Évaluation des scénarios de crise et KPIs."""

    def setUp(self):
        self.dossier_realiste = os.path.join(RACINE, "data", "realiste")
        self.reseau = charger_reseau(self.dossier_realiste)

    def test_comparaison_scenarios(self):
        rapport = comparer_tous_les_scenarios(self.reseau)
        self.assertIn("scenario_normal", rapport)
        self.assertIn("scenario_fermeture_pont", rapport)

        res_pont = rapport["scenario_fermeture_pont"]
        self.assertGreater(res_pont["demandes_devenues_inaccessibles"], 0)
        self.assertGreater(res_pont["pourcentage_demandes_perdues"], 0.0)


if __name__ == "__main__":
    unittest.main()
