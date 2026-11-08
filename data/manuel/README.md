# Jeu de Données Manuel (8 sites)

Ce jeu de données de référence permet de vérifier tous les algorithmes à la main.
- Graphe routier : 8 sites, 14 arcs orientés. S8 n'a pas d'arc entrant (test d'inaccessibilité).
- Graphe fibre : 9 arêtes non orientées. S8 est isolé (permet de valider la forêt couvrante).
- Arbre couvrant minimal (Kruskal/Prim) vérifiable : arêtes choisies S1-S7 (6), S5-S6 (7), S2-S3 (8), S1-S2 (10), S3-S4 (11), S4-S5 (12) -> Coût total = 54.
- Scénarios : fermeture de l'axe S1->S2 forçant la déviation par S1->S3->S2, et panne fibre S1-S2 forçant un raccordement de remplacement.
