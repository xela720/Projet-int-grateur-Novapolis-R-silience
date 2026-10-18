# Graphe de Test : Circuit Absorbant Accessible

Ce graphe contient un circuit absorbant accessible depuis la source A.
- Source : A
- Circuit absorbant : B -> C -> D -> B de poids 3 + (-6) + 1 = -2 < 0.
- Sommet E : accessible depuis D, donc sa distance depuis A est -infini.
- Comportement attendu : Bellman-Ford et Floyd-Warshall doivent détecter le circuit absorbant,
  indiquer qu'il est accessible depuis A, et refuser d'afficher une distance finie pour B, C, D, E.
