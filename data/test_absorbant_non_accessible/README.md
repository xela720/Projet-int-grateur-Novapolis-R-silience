# Graphe de Test : Circuit Absorbant Non Accessible

Ce graphe contient un circuit absorbant non accessible depuis la source A.
- Source : A
- Plus courts chemins depuis A : dist(A)=0, dist(B)=4, dist(C)=6 (chemin A->B->C).
- Circuit absorbant : X -> Y -> Z -> X de poids 1 + 2 - 5 = -2 < 0.
- Comportement attendu : Bellman-Ford lancé depuis A doit renvoyer les distances exactes pour A, B, C,
  tout en signalant que le circuit absorbant n'impacte pas la source A. Floyd-Warshall détecte le cycle
  sur sa diagonale pour X, Y, Z, mais conserve des distances finies entre A, B et C.
