# Novapolis Résilience : Planification des Secours et Réseau Urbain Résilient

Projet intégrateur d'Algorithmique et Théorie des Graphes (ING-APP1-BDML).
Conçu selon les standards stricts du génie logiciel : **zéro bibliothèque externe de graphes** (pas de NetworkX), 100 % bibliothèque standard Python (`csv`, `heapq`, `collections`, `math`, `random`, `time`, `copy`, `argparse`, `unittest`) et `matplotlib` exclusivement pour les rendus graphiques et benchmarks.

---

## 1. Vue d'Ensemble & Architecture Logicielle

Le projet modélise la métropole de **Novapolis** à travers deux graphes distincts partageant les mêmes sommets :
1. **Réseau Routier (Graphe orienté pondéré)** : Modélise les sens de circulation, carrefours, temps normaux et de pointe, capacités et statuts de fermeture.
2. **Réseau de Fibre Optique (Graphe non orienté pondéré)** : Modélise les liaisons physiques de télécommunications avec coûts de déploiement (k€) et statuts de disponibilité.

### Organisation des Fichiers

```text
PROJET_S1/
├── data/                                # 4 jeux de données documentés
│   ├── manuel/                          # Graphe vérifiable à la main (8 sites)
│   ├── realiste/                        # Graphe urbain complet (110 sites, 5 districts)
│   ├── synthetique/                     # Grand réseau d'échelle (1000 sites, seed=42)
│   ├── test_absorbant_accessible/       # Circuit absorbant accessible depuis la source
│   └── test_absorbant_non_accessible/   # Circuit absorbant non accessible depuis la source
├── output/                              # Graphiques scientifiques et animations générés
│   ├── benchmark_plus_courts_chemins.png
│   ├── benchmark_arbres_couvrants.png
│   ├── benchmark_parcours_et_densite.png
│   ├── demo_dijkstra.gif
│   ├── comparaison_avant_apres.png
│   └── reparation_fibre.png
├── src/                                 # Modules algorithmiques indépendants
│   ├── data_manager.py                  # Modèles de graphes, validation CSV, clonage strict
│   ├── generator.py                     # Générateur déterministe des jeux de test
│   ├── accessibility.py                 # Module 1 : DFS, BFS, composantes, cycles orientés
│   ├── shortest_paths.py                # Modules 2 & 3 : Dijkstra, Bellman-Ford, Floyd-Warshall
│   ├── spanning_tree.py                 # Module 4 : Union-Find, Kruskal, Prim, réparation
│   ├── resilience.py                    # Module 5 : KPIs et comparaison multi-scénarios
│   ├── benchmarks.py                    # Protocole de benchmark (5 répétitions, graines fixées)
│   └── visualizer.py                    # Bonus visuel : Animation d'exploration sur carte
├── tests/
│   └── test_all.py                      # Suite complète de tests automatisés (unittest)
├── main.py                              # Interface en ligne de commande (CLI)
├── notebook_projet.ipynb                # Notebook Jupyter intégrant l'ensemble des modules
└── README.md                            # Documentation complète et analyse mathématique
```

---

## 2. Synthèse des Algorithmes et Complexités Théoriques

| Module | Algorithme | Structure de Données | Complexité Théorique | Rôle dans Novapolis |
| :--- | :--- | :--- | :--- | :--- |
| **Module 1** | **DFS** (Parcours en profondeur) | Pile / Récursion | $\mathcal{O}(\|V\| + \|E\|)$ | Détection de cycles, composantes fortement connexes (Tarjan) |
| **Module 1** | **BFS** (Parcours en largeur) | File FIFO (`collections.deque`) | $\mathcal{O}(\|V\| + \|E\|)$ | Itinéraire minimisant le nombre d'arcs, composantes fibre |
| **Module 2** | **Dijkstra** | Tas binaire (`heapq`) | $\mathcal{O}((\|V\| + \|E\|) \log \|V\|)$ | Itinéraire optimal des secours (poids non négatifs) |
| **Module 2** | **Bellman-Ford** | Tableau de relaxation | $\mathcal{O}(\|V\| \cdot \|E\|)$ | Itinéraires avec coûts arbitraires et détection de cycles négatifs |
| **Module 2** | **Floyd-Warshall** | Matrices 2D ($n \times n$) | $\mathcal{O}(\|V\|^3)$ | Plus courts chemins toutes paires et cycles négatifs diagonaux |
| **Module 4** | **Kruskal** | Tri rapide + Union-Find | $\mathcal{O}(\|E\| \log \|E\|)$ | Arbre couvrant minimal (MST) et forêt de fibre optique |
| **Module 4** | **Prim** | Tas binaire (`heapq`) | $\mathcal{O}(\|E\| \log \|V\|)$ | Alternative MST efficace sur graphes denses |
| **Module 4** | **Réparation de panne** | Parcours de coupe bicolore | $\mathcal{O}(\|V\| + \|E\|)$ | Raccordement optimal après coupure d'un câble fibre |

---

## 3. Justifications Algorithmiques & Spécifications Métier

### 3.1 Distinction Rigoureuse des Notions de Connexité (Module 1)
Pour un réseau routier orienté :
- **Connexité ordinaire (faible)** : Deux sommets sont reliés sans tenir compte du sens des flèches.
- **Accessibilité depuis une source** : Ensemble des sommets $v$ atteignables depuis une caserne $s$ en suivant les arcs orientés ouverts.
- **Connexité forte (SCC / CFC)** : Tout sommet peut atteindre n'importe quel autre sommet en suivant les sens autorisés.

### 3.2 Gestion des Circuits Absorbants (Module 3)
Un circuit absorbant (somme des poids strictement négative) rend le calcul de plus court chemin mathématiquement instable ($-\infty$).
- **Cas 1 (Accessible)** : Si le cycle est atteignable depuis la source, le programme propage $-\infty$ (`float('-inf')`) à tous les sommets de son bassin d'attraction et refuse d'afficher une distance finie trompeuse.
- **Cas 2 (Non accessible)** : Si le cycle négatif se situe dans une composante disjointe, Bellman-Ford calcule les distances exactes pour les sommets accessibles et signale l'existence globale du cycle sans corrompre les résultats valides.

### 3.3 Gestion des Coûts Égaux et Multiplicité des Arbres Couvrants (Module 4)
Lorsque plusieurs liaisons de fibre présentent le même coût de pose, le choix de l'arête franchissant la coupe peut différer entre Kruskal et Prim selon l'ordre de tri et la topologie d'exploration. Le poids total minimal obtenu est rigoureusement identique, mais la topologie de l'arbre peut différer.

---

## 4. Guide d'Exécution

### 4.1 Modes Interactifs en Temps Réel (Recommandé pour la démonstration)

Le projet propose **trois modes interactifs** permettant de choisir les scénarios et de visualiser les résultats en direct sans se limiter à des fichiers PNG statiques :

1. **Tableau de bord Web Interactif (HTML5 / Canvas / Zéro dépendance externe)** :
   ```bash
   python main.py --web
   ```
   * Ouvrez votre navigateur sur `http://localhost:8000`.
   * Permet de choisir interactivement le jeu de données et le scénario de crise via des menus déroulants.
   * Carte vectorielle avec **zoom à la molette**, **déplacement panoramique (Pan)** et **survol/clic sur les sites**.
   * Animation fluide du véhicule de secours circulant le long du réseau en temps réel.
   * Affichage dynamique des temps de parcours, retards subis et coupures de routes en rouge pointillé.

2. **Menu Console Interactif (CLI)** :
   ```bash
   python main.py --interactive
   ```
   * Menu textuel interactif permettant de changer de réseau, de tester n'importe quelle intervention et d'ouvrir une fenêtre Matplotlib interactive native.

3. **Intégration directe dans Jupyter Notebook** :
   Ouvrez le notebook :
   ```bash
   jupyter notebook notebook_projet.ipynb
   ```
   La cellule dédiée lance le serveur local en arrière-plan et intègre le tableau de bord interactif directement au cœur du notebook via un `IFrame`.

### 4.2 Ligne de Commande Classique (CLI `main.py`)

```bash
# Diagnostic d'accessibilité sur le jeu réaliste
python main.py --data data/realiste --operation diagnostic

# Évaluation des itinéraires des secours lors de la fermeture d'un pont
python main.py --data data/realiste --scenario scenario_fermeture_pont --operation itineraires

# Comparaison globale des scénarios de résilience
python main.py --data data/realiste --operation resilience

# Exécution complète de tous les modules sur le jeu manuel
python main.py --data data/manuel --operation all

# Lancement des benchmarks scientifiques (génération des 3 graphiques PNG)
python main.py --operation benchmark
```

### 4.3 Lancement des Tests Automatisés

```bash
python -m unittest tests/test_all.py -v
```
