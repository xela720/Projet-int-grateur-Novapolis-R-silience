# Novapolis Résilience : Planification des Secours et Réseau Urbain Résilient

> **Auteurs :** TRAN Huu Loc & PIANA Alexandre  
> **Projet Intégrateur Majeur d'Algorithmique et Théorie des Graphes (EFREI Paris - S1 BDML)**  

---

## 1. Vue d'Ensemble & Dashboard Web Cartographique

Le projet modélise la métropole de **Novapolis** sur la topologie réelle de **Paris & Sud Parisien** (arrondissements 12, 13, 14, Ivry, Kremlin-Bicêtre, Villejuif, jusqu'au **Campus Universitaire Efrei Paris** `SITE_111`).

### Points Forts du Tableau de Bord Web Neubrutaliste
- **Design System Neubrutalisme** : Bordures noires franches (`2.5px solid #000`), ombres dures zéro-flou (`4px 4px 0px #000`), micro-interactions tactiles d'enfoncement (`active: translate(2px, 2px)`), palettes néo-vibrantes (Jaune `#FFE600`, Mint `#00F0A0`, Lilas `#E0E7FF`).
- **Cartographie Réelle Leaflet** : Tuiles officielles **OpenStreetMap Standard** (`tile.openstreetmap.org`), ESRI Canvas, et Google Maps (Plan / Satellite Hybride).
- **Bouton Direct "Grille d'Évaluation & Barème (20 pts)"** : Permet au jury d'auditer et de tester en un clic les 8 critères officiels du barème avec validation live et temps d'exécution.
- **Accès Rapide "Caserne Masséna ➔ Campus Efrei"** : Calcul et traçage instantané de l'itinéraire d'urgence optimal via la RN7 avec affichage du retard relatif en cas d'inondation.
- **Modales d'Analyse Complète** :
  - **Module 1 (Connexité & DFS/BFS)** : Cycles orientés 3 couleurs, composantes connexes fibre, composantes fortement connexes (Tarjan), culs-de-sac et sites isolés.
  - **Module 2 (Comparateur de Chemins)** : Comparaison temps réel Dijkstra vs Bellman-Ford vs Floyd-Warshall vs BFS.
  - **Module 3 (Circuits Absorbants)** : Détection live, bannière clignotante et distinction entre circuit accessible ($-\infty$) et circuit isolé.
  - **Module 4 (Fibre Kruskal / Prim)** : Preuve formelle d'égalité des coûts minimaux (519.2 k€) et simulation de coupure de câble avec raccordement de secours.
  - **Module 5 (Matrice de Résilience)** : Évaluation multi-scénarios sur les 5 indicateurs officiels exigés.
  - **Section 5 (Benchmarks O)** : Visualisation directe des courbes de complexité empiriques vs théoriques.

Si vous utilisez Windows ouvrer le fichier launch_main.bat.

```bash
# Lancement instantané du Tableau de Bord Web sur le port 8000
python main.py --web --port 8000
```
Si erreur python : 
```bash
.\.venv\Scripts\python.exe main.py --web --port 8000
```
Puis ouvrez votre navigateur sur : [http://localhost:8000](http://localhost:8000)

---

## 2. Organisation du Répertoire

```text
PROJET_S1/
├── data/                                # 5 jeux de données CSV documentés et validés
│   ├── manuel/                          # Graphe vérifiable à la main (8 sites)
│   ├── realiste/                        # Graphe urbain complet (111 sites, avec Efrei Paris)
│   ├── synthetique/                     # Réseau d'échelle (1000 sites, seed=42)
│   ├── test_absorbant_accessible/       # Circuit absorbant accessible depuis la source
│   └── test_absorbant_non_accessible/   # Circuit absorbant non accessible depuis la source
├── output/                              # Graphiques scientifiques et animations générés
│   ├── benchmark_plus_courts_chemins.png
│   ├── benchmark_arbres_couvrants.png
│   ├── benchmark_parcours_et_densite.png
│   ├── demo_dijkstra.gif
│   ├── comparaison_avant_apres.png
│   └── reparation_fibre.png
├── screenshots/                         # Captures d'écran du Dashboard Web Neubrutaliste
├── src/                                 # Modules algorithmiques purs (0 NetworkX)
│   ├── data_manager.py                  # Modèles de graphes, validation CSV, clonage strict
│   ├── generator.py                     # Générateur déterministe des jeux de test
│   ├── accessibility.py                 # Module 1 : DFS, BFS, composantes, cycles orientés
│   ├── shortest_paths.py                # Modules 2 & 3 : Dijkstra, Bellman-Ford, Floyd-Warshall
│   ├── spanning_tree.py                 # Module 4 : Union-Find, Kruskal, Prim, réparation
│   ├── resilience.py                    # Module 5 : KPIs et comparaison multi-scénarios
│   ├── benchmarks.py                    # Protocole scientifique (5 runs, seed fixée 42)
│   ├── visualizer.py                    # Rendu graphique et animation d'itinéraires
│   └── web_dashboard.py                 # Serveur HTTP/JSON & Dashboard Neubrutaliste complet
├── tests/
│   ├── test_all.py                      # 17 tests d'intégration des 5 modules
│   └── test_graphe.py                   # 11 tests unitaires bas niveau
├── main.py                              # CLI unifié (--cli, --web, --benchmark, etc.)
├── notebook_projet.ipynb                # Rapport académique Jupyter complet
├── PROJET_NOVAPOLIS_RAPPORT.ipynb       # Copie conforme pour le rendu académique
├── SOUTENANCE_ORALE_12MIN.md            # Guide minuté de soutenance (12 min + Q&A)
└── README.md                            # Documentation complète du projet
```

---

## 3. Synthèse des Algorithmes et Complexités Théoriques

| Module | Algorithme | Structure de Données | Complexité Théorique | Application dans Novapolis |
| :--- | :--- | :--- | :--- | :--- |
| **Module 1** | **DFS** (Parcours en profondeur) | Pile d'appels récursive | $\mathcal{O}(\|V\| + \|E\|)$ | Détection de cycles (3 couleurs), composantes fortement connexes (Tarjan) |
| **Module 1** | **BFS** (Parcours en largeur) | File FIFO (`collections.deque`) | $\mathcal{O}(\|V\| + \|E\|)$ | Itinéraire à nombre d'arcs minimal, composantes connexes non orientées |
| **Module 2** | **Dijkstra** | Tas binaire (`heapq`) | $\mathcal{O}((\|V\| + \|E\|) \log \|V\|)$ | Plus court chemin en temps pour véhicules d'urgence (poids $\ge 0$) |
| **Module 2** | **Bellman-Ford** | Relaxation successive de vecteurs | $\mathcal{O}(\|V\| \cdot \|E\|)$ | Chemins avec poids arbitraires et détection de cycles négatifs |
| **Module 2** | **Floyd-Warshall** | Matrices 2D ($n \times n$) | $\mathcal{O}(\|V\|^3)$ | Plus courts chemins toutes paires et détection de diagonales négatives |
| **Module 3** | **Propagation $-\infty$** | BFS sélectif depuis cycles absorbants | $\mathcal{O}(\|V\| + \|E\|)$ | Identification exacte des sommets impactés par un circuit absorbant |
| **Module 4** | **Kruskal** | Tri rapide + Union-Find (rang & compression) | $\mathcal{O}(\|E\| \log \|E\|)$ | Arbre couvrant minimal (MST) pour le réseau fibre optique |
| **Module 4** | **Prim** | File de priorité / Tas binaire (`heapq`) | $\mathcal{O}(\|E\| \log \|V\|)$ | Alternative d'arbre couvrant minimal optimisée pour graphes denses |
| **Module 4** | **Coupe Bicolore** | BFS bicolore + recherche d'arête minimale | $\mathcal{O}(\|V\| + \|E\|)$ | Raccordement d'urgence optimal après rupture d'un câble fibre |
| **Module 5** | **Évaluateur Résilience** | Modélisation multi-scénarios sur clones | $\mathcal{O}(S \cdot (\|V\|+\|E\| \log \|V\|))$ | Calcul des 5 métriques exigées sous 4 scénarios de crise |

---

## 4. Spécifications Métier & Justifications Théoriques

### 4.1 Connexité Routière vs Connexité Fibre (Module 1)
- Le **réseau routier** est **orienté** : la présence d'une voie de $u$ vers $v$ n'implique pas la réciproque (sens uniques). Nous analysons l'accessibilité orientée $s \rightsquigarrow v$ et la forte connexité (Tarjan).
- Le **réseau fibre** est **non-orienté** : les liaisons physiques sont bidirectionnelles. Nous mesurons le nombre de composantes connexes (1 composante en état normal).

### 4.2 Traitement des Circuits Absorbants (Module 3)
Un circuit absorbant (somme des poids $< 0$) rend le problème du plus court chemin mal posé ($-\infty$).
- **Cycle accessible depuis la source** : Bellman-Ford détecte le cycle à la $|V|$-ième étape. Une propagation BFS assigne `float('-inf')` à tous les sommets atteignables depuis ce cycle.
- **Cycle non accessible depuis la source** : Si le cycle est dans une composante disjointe, il n'altère pas les distances des secours. Les distances réelles sont calculées et affichées, et une alerte signale la présence du cycle isolé.

### 4.3 Multiplicité des Arbres Couvrants et Égalité des Coûts (Module 4)
- Lorsque plusieurs arêtes possèdent le même coût en k€, Kruskal et Prim peuvent choisir des arêtes différentes si les ordres de tri ou de parcours diffèrent.
- **Résultat formel** : Le coût total minimal est rigoureusement identique (**519.2 k€** sur le jeu réaliste).

---

## 5. Guide d'Exécution & Commandes CLI

### 5.1 Lancement du Serveur Web (Recommandé)
```bash
python main.py --web --port 8000
```
Accès : [http://localhost:8000](http://localhost:8000)

### 5.2 Ligne de Commande Classique
```bash
# Diagnostic topologique (Module 1)
python main.py --data data/realiste --operation diagnostic

# Évaluation des itinéraires des secours (Module 2)
python main.py --data data/realiste --scenario scenario_fermeture_pont --operation itineraires

# Comparaison des scénarios de résilience (Module 5)
python main.py --data data/realiste --operation resilience

# Exécution complète de tous les modules sur le jeu manuel
python main.py --data data/manuel --operation all

# Lancement des benchmarks scientifiques (Module 5 & Section 5)
python main.py --operation benchmark
```

### 5.3 Lancement de la Suite de Tests Automatisés (31 Tests)
```bash
python -m unittest discover tests -v
```
*Taux de réussite : **100 %** (31/31 tests réussis en 0.12 s).*

---

## 6. Rapports et Documents Pédagogiques

- **[RAPPORT_FINAL_NOVAPOLIS.pdf](RAPPORT_FINAL_NOVAPOLIS.pdf)** : version figée destinée à la lecture. Elle reprend les méthodes, résultats, limites et recommandations sur 13 pages.
- **[RAPPORT_AUDIT_QA.md](RAPPORT_AUDIT_QA.md)** : rapport de recette présentant les tests fonctionnels, l’évaluation de l’interface, les scénarios de crise vérifiés et les preuves visuelles associées.
- **[PROJET_NOVAPOLIS_RAPPORT.ipynb](PROJET_NOVAPOLIS_RAPPORT.ipynb)** : Notebook Jupyter de démonstration regroupant les calculs, visualisations, benchmarks et tests sans interfaces.
