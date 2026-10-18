"""Générateur complet des jeux de données pour le projet Novapolis Résilience.

Ce module crée les 4 jeux de données exigés par le cahier des charges :
1. data/manuel/ : petit graphe vérifiable à la main (8 sites)
2. data/realiste/ : réseau urbain réaliste documenté (110 sites, 5 districts)
3. data/synthetique/ : grand réseau généré de 1000 sites avec graine fixée (seed 42)
4. data/test_absorbant_accessible/ et data/test_absorbant_non_accessible/ :
   deux graphes de test spécifiques pour valider Bellman-Ford et Floyd-Warshall
   face aux circuits absorbants (accessibles et non accessibles).
"""

import os
import csv
import math
import random


def creer_dossier_si_absent(chemin):
    """Crée le dossier spécifié s'il n'existe pas déjà."""
    if not os.path.exists(chemin):
        os.makedirs(chemin)


def ecrire_csv(chemin_fichier, entetes, lignes):
    """Écrit une liste de dictionnaires ou de tuples dans un fichier CSV avec encodage UTF-8."""
    with open(chemin_fichier, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(entetes)
        for ligne in lignes:
            writer.writerow(ligne)


def generer_jeu_manuel(base_dir="data/manuel"):
    """Génère le petit jeu de données vérifiable à la main (8 sites).

    Ce graphe permet de valider sur papier tous les algorithmes :
    - DFS / BFS : S8 est un cul-de-sac dirigé sans retour ou isolé.
    - Dijkstra / Bellman-Ford : calculs pas à pas de plus courts chemins.
    - Kruskal / Prim : calcul de l'arbre couvrant sur la composante connexe principale.
    - Scénarios : fermeture de l'axe S1->S2 et panne de la liaison fibre S1-S2.
    """
    creer_dossier_si_absent(base_dir)

    # 1. Sites
    sites_entetes = ["id", "nom", "type", "longitude", "latitude"]
    sites_lignes = [
        ["S1", "Caserne Centrale", "caserne", 2.3000, 48.8500],
        ["S2", "Hopital Saint-Paul", "hopital", 2.3200, 48.8600],
        ["S3", "Quartier Nord", "quartier", 2.3100, 48.8700],
        ["S4", "Centre Telecom", "telecom", 2.3400, 48.8550],
        ["S5", "Ecole Victor Hugo", "ecole", 2.3300, 48.8400],
        ["S6", "Quartier Sud", "quartier", 2.3050, 48.8350],
        ["S7", "Caserne Ouest", "caserne", 2.2800, 48.8500],
        ["S8", "Poste Avance Isole", "poste_isole", 2.3700, 48.8800],
    ]
    ecrire_csv(os.path.join(base_dir, "sites.csv"), sites_entetes, sites_lignes)

    # 2. Routes (orientées)
    routes_entetes = ["u", "v", "temps_normal", "temps_pointe", "statut", "type_voie", "capacite"]
    routes_lignes = [
        ["S1", "S2", 5.0, 8.0, "ouvert", "artere", 1500],
        ["S2", "S1", 5.0, 8.0, "ouvert", "artere", 1500],
        ["S1", "S3", 7.0, 12.0, "ouvert", "avenue", 1200],
        ["S3", "S2", 3.0, 5.0, "ouvert", "rue_locale", 800],
        ["S2", "S4", 4.0, 6.0, "ouvert", "rue_locale", 800],
        ["S4", "S2", 4.0, 6.0, "ouvert", "rue_locale", 800],
        ["S4", "S5", 6.0, 10.0, "ouvert", "artere", 1400],
        ["S5", "S6", 4.0, 7.0, "ouvert", "rue_locale", 700],
        ["S6", "S1", 8.0, 14.0, "ouvert", "artere", 1300],
        ["S1", "S7", 3.0, 5.0, "ouvert", "boulevard", 1800],
        ["S7", "S1", 3.0, 5.0, "ouvert", "boulevard", 1800],
        ["S7", "S6", 6.0, 9.0, "ouvert", "rue_locale", 900],
        ["S3", "S5", 9.0, 15.0, "ouvert", "artere", 1100],
        ["S8", "S3", 10.0, 15.0, "ouvert", "rue_locale", 500],  # S8 peut aller vers S3, mais aucun arc n'entre dans S8
    ]
    ecrire_csv(os.path.join(base_dir, "routes.csv"), routes_entetes, routes_lignes)

    # 3. Fibre (non orientée)
    fibre_entetes = ["u", "v", "cost", "statut"]
    fibre_lignes = [
        ["S1", "S2", 10.0, "actif"],
        ["S2", "S3", 8.0, "actif"],
        ["S1", "S7", 6.0, "actif"],
        ["S2", "S4", 15.0, "actif"],
        ["S4", "S5", 12.0, "actif"],
        ["S5", "S6", 7.0, "actif"],
        ["S6", "S7", 14.0, "actif"],
        ["S1", "S5", 20.0, "actif"],
        ["S3", "S4", 11.0, "actif"],
        # S8 non relié volontairement pour tester la forêt couvrante (composantes non raccordées)
    ]
    ecrire_csv(os.path.join(base_dir, "fibre.csv"), fibre_entetes, fibre_lignes)

    # 4. Demandes
    demandes_entetes = ["id", "origine", "destination", "type", "priorite"]
    demandes_lignes = [
        ["D1", "S1", "S3", "incendie", 1],
        ["D2", "S1", "S5", "urgence_medicale", 1],
        ["D3", "S7", "S6", "accident", 2],
        ["D4", "S1", "S8", "secours", 1],  # Inaccessible pour tester la détection d'inaccessibilité
    ]
    ecrire_csv(os.path.join(base_dir, "demandes.csv"), demandes_entetes, demandes_lignes)

    # 5. Scenarios
    scenarios_entetes = ["scenario_id", "type_element", "u", "v", "action", "valeur"]
    scenarios_lignes = [
        ["scenario_normal", "aucun", "none", "none", "baseline", "0"],
        ["scenario_fermeture_axe", "route", "S1", "S2", "fermer", "0"],
        ["scenario_panne_fibre", "fibre", "S1", "S2", "fermer", "0"],
    ]
    ecrire_csv(os.path.join(base_dir, "scenarios.csv"), scenarios_entetes, scenarios_lignes)

    # 6. Documentation
    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Jeu de Données Manuel (8 sites)\n\n"
                "Ce jeu de données de référence permet de vérifier tous les algorithmes à la main.\n"
                "- Graphe routier : 8 sites, 14 arcs orientés. S8 n'a pas d'arc entrant (test d'inaccessibilité).\n"
                "- Graphe fibre : 9 arêtes non orientées. S8 est isolé (permet de valider la forêt couvrante).\n"
                "- Arbre couvrant minimal (Kruskal/Prim) vérifiable : arêtes choisies S1-S7 (6), S5-S6 (7), S2-S3 (8), S1-S2 (10), S3-S4 (11), S4-S5 (12) -> Coût total = 54.\n"
                "- Scénarios : fermeture de l'axe S1->S2 forçant la déviation par S1->S3->S2, et panne fibre S1-S2 forçant un raccordement de remplacement.\n")


SITES_EXACTS_PARIS = [
    # --- DISTRICT 1 : CENTRE-VILLE & CITÉ (25 sites) ---
    ("SITE_001", "Caserne Châtelet (État-Major BSPP)", "caserne", 2.3472, 48.8575),
    ("SITE_002", "Hôpital Hôtel-Dieu Paris", "hopital", 2.3490, 48.8546),
    ("SITE_003", "Hub Core Châtelet - Les Halles", "telecom", 2.3458, 48.8615),
    ("SITE_004", "Lycée Henri-IV", "ecole", 2.3481, 48.8461),
    ("SITE_005", "Lycée Charlemagne", "ecole", 2.3608, 48.8542),
    ("SITE_006", "Quartier Place des Vosges - Marais", "quartier", 2.3655, 48.8556),
    ("SITE_007", "Quartier Hôtel de Ville", "quartier", 2.3522, 48.8566),
    ("SITE_008", "Quartier Sainte-Chapelle (Cité)", "quartier", 2.3450, 48.8554),
    ("SITE_009", "Quartier Musée du Louvre", "quartier", 2.3376, 48.8606),
    ("SITE_010", "Quartier Beaubourg - Centre Pompidou", "quartier", 2.3522, 48.8606),
    ("SITE_011", "Quartier Sentier - Rue Réaumur", "quartier", 2.3490, 48.8672),
    ("SITE_012", "Quartier Saint-Gervais", "quartier", 2.3556, 48.8558),
    ("SITE_013", "Quartier Forum des Halles", "quartier", 2.3480, 48.8605),
    ("SITE_014", "Quartier Rue de Rivoli", "quartier", 2.3560, 48.8560),
    ("SITE_015", "Quartier Port de l'Arsenal", "quartier", 2.3670, 48.8510),
    ("SITE_016", "Quartier Parvis Notre-Dame", "quartier", 2.3499, 48.8530),
    ("SITE_017", "Quartier Place Dauphine - Pont Neuf", "quartier", 2.3430, 48.8566),
    ("SITE_018", "Quartier Domaine du Palais-Royal", "quartier", 2.3369, 48.8638),
    ("SITE_019", "Quartier Église Saint-Merri", "quartier", 2.3510, 48.8590),
    ("SITE_020", "Quartier Palais Brongniart (Bourse)", "quartier", 2.3412, 48.8690),
    ("SITE_021", "Quartier Place des Victoires", "quartier", 2.3400, 48.8660),
    ("SITE_022", "Quartier Grand Rex - Bonne-Nouvelle", "quartier", 2.3505, 48.8705),
    ("SITE_023", "Quartier Arts-et-Métiers (CNAM)", "quartier", 2.3585, 48.8660),
    ("SITE_024", "Quartier Marché des Enfants-Rouges", "quartier", 2.3620, 48.8635),
    ("SITE_025", "Quartier Fontaine Saint-Michel", "quartier", 2.3440, 48.8530),

    # --- DISTRICT 2 : NORD (10e, 18e, 9e) (20 sites) ---
    ("SITE_026", "Caserne Montmartre - Carpeaux", "caserne", 2.3364, 48.8906),
    ("SITE_027", "Hôpital Lariboisière", "hopital", 2.3533, 48.8826),
    ("SITE_028", "Hub Télécom Gare du Nord", "telecom", 2.3553, 48.8809),
    ("SITE_029", "Lycée Condorcet", "ecole", 2.3276, 48.8752),
    ("SITE_030", "Collège-Lycée Jacques-Decour", "ecole", 2.3442, 48.8814),
    ("SITE_031", "Quartier Basilique du Sacré-Cœur", "quartier", 2.3431, 48.8867),
    ("SITE_032", "Quartier Gare de l'Est", "quartier", 2.3590, 48.8768),
    ("SITE_033", "Quartier Place Pigalle", "quartier", 2.3370, 48.8822),
    ("SITE_034", "Quartier Rue de la Chapelle", "quartier", 2.3595, 48.8850),
    ("SITE_035", "Quartier Barbès-Rochechouart", "quartier", 2.3499, 48.8835),
    ("SITE_036", "Quartier La Goutte d'Or", "quartier", 2.3540, 48.8865),
    ("SITE_037", "Quartier Porte de Clignancourt", "quartier", 2.3445, 48.8980),
    ("SITE_038", "Quartier Grandes-Carrières - Cimetière Montmartre", "quartier", 2.3320, 48.8890),
    ("SITE_039", "Quartier Porte de Saint-Ouen", "quartier", 2.3280, 48.8975),
    ("SITE_040", "Quartier Mairie du 18e (Jules Joffrin)", "quartier", 2.3450, 48.8925),
    ("SITE_041", "Quartier Lamarck-Caulaincourt", "quartier", 2.3385, 48.8898),
    ("SITE_042", "Quartier Marcadet-Poissonniers", "quartier", 2.3505, 48.8915),
    ("SITE_043", "Quartier Place des Abbesses", "quartier", 2.3386, 48.8845),
    ("SITE_044", "Quartier Place Blanche - Moulin Rouge", "quartier", 2.3323, 48.8841),
    ("SITE_045", "Quartier Palais Garnier (Opéra)", "quartier", 2.3316, 48.8719),

    # --- DISTRICT 3 : SUD (13e, 14e, 5e, 6e) (20 sites) ---
    ("SITE_046", "Caserne Masséna (13e)", "caserne", 2.3695, 48.8218),
    ("SITE_047", "Hôpital Pitié-Salpêtrière", "hopital", 2.3644, 48.8392),
    ("SITE_048", "Hub Télécom Place d'Italie", "telecom", 2.3558, 48.8315),
    ("SITE_049", "Lycée Lavoisier", "ecole", 2.3385, 48.8415),
    ("SITE_050", "Lycée Montaigne - Jardin du Luxembourg", "ecole", 2.3355, 48.8458),
    ("SITE_051", "Quartier Mairie du 13e", "quartier", 2.3550, 48.8310),
    ("SITE_052", "Quartier Manufacture des Gobelins", "quartier", 2.3525, 48.8360),
    ("SITE_053", "Quartier Place Victor et Hélène Basch (Alésia)", "quartier", 2.3270, 48.8280),
    ("SITE_054", "Quartier Cité Universitaire - Parc Montsouris", "quartier", 2.3385, 48.8220),
    ("SITE_055", "Quartier Olympiades - Tolbiac", "quartier", 2.3660, 48.8270),
    ("SITE_056", "Quartier Porte d'Orléans", "quartier", 2.3260, 48.8205),
    ("SITE_057", "Quartier Place Denfert-Rochereau", "quartier", 2.3325, 48.8340),
    ("SITE_058", "Quartier Pôle Gare d'Austerlitz", "quartier", 2.3660, 48.8420),
    ("SITE_059", "Quartier La Butte-aux-Cailles", "quartier", 2.3515, 48.8280),
    ("SITE_060", "Quartier Maison-Blanche", "quartier", 2.3590, 48.8235),
    ("SITE_061", "Quartier Bibliothèque François-Mitterrand (BNF)", "quartier", 2.3760, 48.8340),
    ("SITE_062", "Quartier Boulevard Auguste-Blanqui", "quartier", 2.3440, 48.8315),
    ("SITE_063", "Quartier Hôpital Cochin - Port-Royal", "quartier", 2.3395, 48.8385),
    ("SITE_064", "Quartier Square René-Le Gall", "quartier", 2.3500, 48.8335),
    ("SITE_065", "Quartier Tour & Gare Montparnasse", "quartier", 2.3200, 48.8415),

    # --- DISTRICT 4 : EST (11e, 12e, 20e) (20 sites) ---
    ("SITE_066", "Caserne Chaligny (12e)", "caserne", 2.3842, 48.8492),
    ("SITE_067", "Hôpital Saint-Antoine", "hopital", 2.3845, 48.8504),
    ("SITE_068", "Hub Télécom Place de la Nation", "telecom", 2.3959, 48.8484),
    ("SITE_069", "Lycée Hélène Boucher", "ecole", 2.4082, 48.8475),
    ("SITE_070", "Lycée Paul Valéry", "ecole", 2.4115, 48.8423),
    ("SITE_071", "Quartier Colonne de Juillet - Place de la Bastille", "quartier", 2.3690, 48.8530),
    ("SITE_072", "Quartier Mairie du 11e - Place Léon Blum", "quartier", 2.3800, 48.8580),
    ("SITE_073", "Quartier Parc de Belleville", "quartier", 2.3850, 48.8710),
    ("SITE_074", "Quartier Cimetière du Père-Lachaise", "quartier", 2.3930, 48.8615),
    ("SITE_075", "Quartier Accor Arena - Parc de Bercy", "quartier", 2.3785, 48.8385),
    ("SITE_076", "Quartier Ménilmontant", "quartier", 2.3880, 48.8660),
    ("SITE_077", "Quartier Cour Saint-Émilion (Bercy Village)", "quartier", 2.3860, 48.8325),
    ("SITE_078", "Quartier Place Félix Éboué (Daumesnil)", "quartier", 2.3950, 48.8395),
    ("SITE_079", "Quartier Gare de Lyon - Tour de l'Horloge", "quartier", 2.3735, 48.8445),
    ("SITE_080", "Quartier Avenue Ledru-Rollin", "quartier", 2.3745, 48.8510),
    ("SITE_081", "Quartier Marché d'Aligre", "quartier", 2.3815, 48.8505),
    ("SITE_082", "Quartier Rue de Picpus", "quartier", 2.4010, 48.8440),
    ("SITE_083", "Quartier Bel-Air - Coulée Verte", "quartier", 2.4085, 48.8400),
    ("SITE_084", "Quartier Église Saint-Germain de Charonne", "quartier", 2.4035, 48.8550),
    ("SITE_085", "Quartier Cours de Vincennes - Porte de Vincennes", "quartier", 2.4130, 48.8470),

    # --- DISTRICT 5 : OUEST (7e, 8e, 15e, 16e) (20 sites) ---
    ("SITE_086", "Caserne Dauphine (16e)", "caserne", 2.2742, 48.8688),
    ("SITE_087", "Hôpital Européen Georges-Pompidou", "hopital", 2.2736, 48.8394),
    ("SITE_088", "Hub Télécom Place de l'Étoile", "telecom", 2.2965, 48.8778),
    ("SITE_089", "Lycée Janson-de-Sailly", "ecole", 2.2779, 48.8647),
    ("SITE_090", "Lycée Jean-Baptiste Say", "ecole", 2.2635, 48.8449),
    ("SITE_091", "Quartier Esplanade du Trocadéro", "quartier", 2.2880, 48.8625),
    ("SITE_092", "Quartier Village de Passy", "quartier", 2.2800, 48.8580),
    ("SITE_093", "Quartier Village d'Auteuil", "quartier", 2.2660, 48.8480),
    ("SITE_094", "Quartier Palais des Congrès - Porte Maillot", "quartier", 2.2830, 48.8785),
    ("SITE_095", "Quartier Avenue des Champs-Élysées", "quartier", 2.3080, 48.8700),
    ("SITE_096", "Quartier Monument Arc de Triomphe", "quartier", 2.2950, 48.8738),
    ("SITE_097", "Quartier Jardin du Ranelagh - La Muette", "quartier", 2.2750, 48.8585),
    ("SITE_098", "Quartier Place Victor Hugo", "quartier", 2.2850, 48.8700),
    ("SITE_099", "Quartier Tour Eiffel - Champ-de-Mars", "quartier", 2.2945, 48.8584),
    ("SITE_100", "Quartier Maison de Radio France", "quartier", 2.2780, 48.8525),
    ("SITE_101", "Quartier Porte de Saint-Cloud - Exelmans", "quartier", 2.2610, 48.8410),
    ("SITE_102", "Quartier Pont Mirabeau (Rive Gauche)", "quartier", 2.2760, 48.8470),
    ("SITE_103", "Quartier Centre Beaugrenelle", "quartier", 2.2825, 48.8485),
    ("SITE_104", "Quartier Rue de la Convention (15e)", "quartier", 2.2970, 48.8370),
    ("SITE_105", "Quartier Esplanade des Invalides", "quartier", 2.3120, 48.8565),

    # --- PÉRIPHÉRIE / VAL-DE-MARNE (5 sites) ---
    ("SITE_106", "Poste Secours Bords de Marne (Saint-Maur)", "caserne", 2.4500, 48.8050),
    ("SITE_107", "Quartier Port de Bonneuil", "quartier", 2.4650, 48.7850),
    ("SITE_108", "Centre Fret Plateforme Sud-Est", "zone_logistique", 2.4700, 48.7750),
    ("SITE_109", "Station Épuration Presqu'île", "infrastructure", 2.4850, 48.7650),
    ("SITE_110", "Refuge Butte Isolée", "refuge", 2.4900, 48.7550),
    ("SITE_111", "Efrei Paris - Campus Villejuif", "ecole", 2.3637, 48.7887),
]



def generer_jeu_realiste(base_dir="data/realiste", nb_sites=111, seed=42):
    """Génère le jeu de données urbain réaliste documenté (111 sites géoréférencés à Paris & Campus Efrei)."""
    import rebuild_realistic_paris
    rebuild_realistic_paris.DATA_DIR = os.path.abspath(base_dir)
    rebuild_realistic_paris.main()


def generer_jeu_synthetique(base_dir="data/synthetique", nb_sites=1000, seed=42):
    """Génère le grand réseau synthétique (1000 sites) pour les benchmarks de performance.

    - Reproductibilité absolue : graine fixée à 42.
    - Topologie planaire spatialement distribuée en clusters urbains.
    - Plus de 3500 arcs routiers et 2500 arêtes de fibre.
    - Idéal pour comparer les complexités O(|V| + |E|), O(|E| log |V|), O(|V||E|) et O(|V|^3).
    """
    creer_dossier_si_absent(base_dir)
    random.seed(seed)

    nb_clusters = 10
    centres = [
        (random.uniform(2.10, 2.60), random.uniform(48.70, 49.00))
        for _ in range(nb_clusters)
    ]

    sites = []
    types_repartition = [
        ("caserne", 30),
        ("hopital", 25),
        ("telecom", 45),
        ("ecole", 150),
        ("quartier", 750),
    ]
    types_liste = []
    for t, count in types_repartition:
        types_liste.extend([t] * count)
    random.shuffle(types_liste)

    for i in range(nb_sites):
        s_id = f"SYNTH_{i+1:04d}"
        s_type = types_liste[i]
        s_nom = f"Site_{s_type}_{i+1}"
        # Choix d'un cluster
        c_lon, c_lat = random.choice(centres)
        lon = round(c_lon + random.gauss(0, 0.025), 5)
        lat = round(c_lat + random.gauss(0, 0.020), 5)
        sites.append({"id": s_id, "nom": s_nom, "type": s_type, "lon": lon, "lat": lat})

    sites_entetes = ["id", "nom", "type", "longitude", "latitude"]
    sites_lignes = [[s["id"], s["nom"], s["type"], s["lon"], s["lat"]] for s in sites]
    ecrire_csv(os.path.join(base_dir, "sites.csv"), sites_entetes, sites_lignes)

    # Grille spatiale pour accélérer la recherche des voisins (O(N) au lieu de O(N^2))
    grille = {}
    taille_case = 0.04
    for idx, s in enumerate(sites):
        cx = int(s["lon"] / taille_case)
        cy = int(s["lat"] / taille_case)
        grille.setdefault((cx, cy), []).append(idx)

    def dist_approx(i, j):
        dx = (sites[i]["lon"] - sites[j]["lon"]) * 72.0
        dy = (sites[i]["lat"] - sites[j]["lat"]) * 111.0
        return math.sqrt(dx * dx + dy * dy)

    routes_set = set()
    routes_lignes = []

    fibre_set = set()
    fibre_lignes = []

    for i, s in enumerate(sites):
        cx = int(s["lon"] / taille_case)
        cy = int(s["lat"] / taille_case)
        # Candidats dans les 9 cases voisines
        candidats = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidats.extend(grille.get((cx + dx, cy + dy), []))

        # Trier les candidats par distance
        candidats = [c for c in candidats if c != i]
        candidats.sort(key=lambda c: dist_approx(i, c))

        # Connexions routières vers les 4 plus proches
        for c in candidats[:4]:
            d = max(0.5, dist_approx(i, c))
            t_norm = max(1.0, round(d * 1.8, 2))
            t_pte = round(t_norm * 1.5, 2)
            u = s["id"]
            v = sites[c]["id"]
            if (u, v) not in routes_set:
                routes_set.add((u, v))
                routes_lignes.append([u, v, t_norm, t_pte, "ouvert", "route_standard", 1000])
            # Double sens à 85%
            if random.random() < 0.85:
                if (v, u) not in routes_set:
                    routes_set.add((v, u))
                    routes_lignes.append([v, u, t_norm, t_pte, "ouvert", "route_standard", 1000])

        # Connexions fibre optique vers les 3 plus proches
        for c in candidats[:3]:
            u = s["id"]
            v = sites[c]["id"]
            paire = tuple(sorted([u, v]))
            if paire not in fibre_set:
                fibre_set.add(paire)
                cout = round(max(5.0, dist_approx(i, c) * 12.0), 1)
                fibre_lignes.append([paire[0], paire[1], cout, "actif"])

    routes_entetes = ["u", "v", "temps_normal", "temps_pointe", "statut", "type_voie", "capacite"]
    ecrire_csv(os.path.join(base_dir, "routes.csv"), routes_entetes, routes_lignes)

    fibre_entetes = ["u", "v", "cost", "statut"]
    ecrire_csv(os.path.join(base_dir, "fibre.csv"), fibre_entetes, fibre_lignes)

    # 4. Demandes (50 demandes aléatoires avec casernes comme origine)
    casernes = [s["id"] for s in sites if s["type"] == "caserne"]
    quartiers = [s["id"] for s in sites if s["type"] == "quartier"]

    demandes_lignes = []
    for i in range(1, 51):
        d_id = f"D_SYNTH_{i:03d}"
        cas = random.choice(casernes)
        dest = random.choice(quartiers)
        demandes_lignes.append([d_id, cas, dest, "urgence", random.choice([1, 2, 3])])

    demandes_entetes = ["id", "origine", "destination", "type", "priorite"]
    ecrire_csv(os.path.join(base_dir, "demandes.csv"), demandes_entetes, demandes_lignes)

    # 5. Scenarios
    scenarios_entetes = ["scenario_id", "type_element", "u", "v", "action", "valeur"]
    scenarios_lignes = [
        ["scenario_normal", "aucun", "none", "none", "baseline", "0"],
        ["scenario_coupure_multiple", "route", routes_lignes[0][0], routes_lignes[0][1], "fermer", "0"],
        ["scenario_coupure_multiple", "route", routes_lignes[10][0], routes_lignes[10][1], "fermer", "0"],
        ["scenario_panne_fibre", "fibre", fibre_lignes[0][0], fibre_lignes[0][1], "fermer", "0"],
    ]
    ecrire_csv(os.path.join(base_dir, "scenarios.csv"), scenarios_entetes, scenarios_lignes)

    # 6. Documentation
    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Jeu de Données Synthétique (1000 sites)\n\n"
                "Généré de manière déterministe avec la graine aléatoire fixée à 42.\n"
                f"- Nombre de sites : {nb_sites}\n"
                f"- Nombre d'arcs routiers : {len(routes_lignes)}\n"
                f"- Nombre d'arêtes fibre : {len(fibre_lignes)}\n"
                "- Conçu pour les benchmarks d'algorithmes (DFS/BFS, Kruskal, Prim, Dijkstra, Bellman-Ford).\n")


def generer_jeu_absorbant_accessible(base_dir="data/test_absorbant_accessible"):
    """Génère un graphe avec un circuit absorbant accessible depuis la source A.

    Topologie :
    A (source) -> B (coût 2)
    B -> C (coût 3)
    C -> D (coût -6)
    D -> B (coût 1)   --> Circuit B -> C -> D -> B de poids 3 - 6 + 1 = -2 < 0 !
    D -> E (coût 2)   --> Le sommet E est accessible après le circuit absorbant.
    F -> G (coût 1)   --> Composante indépendante non perturbée.
    """
    creer_dossier_si_absent(base_dir)

    sites_entetes = ["id", "nom", "type", "longitude", "latitude"]
    sites_lignes = [
        ["A", "Source Principale", "source", 0.0, 0.0],
        ["B", "Entree Circuit", "noeud", 1.0, 0.0],
        ["C", "Sommet Negatif 1", "noeud", 2.0, 1.0],
        ["D", "Sommet Negatif 2", "noeud", 2.0, -1.0],
        ["E", "Destination Puits", "destination", 3.0, 0.0],
        ["F", "Site Independant 1", "autre", 5.0, 5.0],
        ["G", "Site Independant 2", "autre", 6.0, 5.0],
    ]
    ecrire_csv(os.path.join(base_dir, "sites.csv"), sites_entetes, sites_lignes)

    routes_entetes = ["u", "v", "temps_normal", "temps_pointe", "statut", "type_voie", "capacite"]
    routes_lignes = [
        ["A", "B", 2.0, 2.0, "ouvert", "artificiel", 1000],
        ["B", "C", 3.0, 3.0, "ouvert", "artificiel", 1000],
        ["C", "D", -6.0, -6.0, "ouvert", "artificiel", 1000],  # Poids négatif
        ["D", "B", 1.0, 1.0, "ouvert", "artificiel", 1000],   # Somme du cycle = -2
        ["D", "E", 2.0, 2.0, "ouvert", "artificiel", 1000],   # E est accessible depuis le cycle absorbant
        ["F", "G", 1.0, 1.0, "ouvert", "artificiel", 1000],
    ]
    ecrire_csv(os.path.join(base_dir, "routes.csv"), routes_entetes, routes_lignes)

    fibre_entetes = ["u", "v", "cost", "statut"]
    fibre_lignes = [
        ["A", "B", 5.0, "actif"],
        ["B", "C", 5.0, "actif"],
        ["C", "D", 5.0, "actif"],
        ["D", "E", 5.0, "actif"],
    ]
    ecrire_csv(os.path.join(base_dir, "fibre.csv"), fibre_entetes, fibre_lignes)

    demandes_entetes = ["id", "origine", "destination", "type", "priorite"]
    demandes_lignes = [
        ["D_ACC_1", "A", "E", "test_circuit_absorbant", 1],
    ]
    ecrire_csv(os.path.join(base_dir, "demandes.csv"), demandes_entetes, demandes_lignes)

    scenarios_entetes = ["scenario_id", "type_element", "u", "v", "action", "valeur"]
    scenarios_lignes = [
        ["scenario_normal", "aucun", "none", "none", "baseline", "0"]
    ]
    ecrire_csv(os.path.join(base_dir, "scenarios.csv"), scenarios_entetes, scenarios_lignes)

    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Graphe de Test : Circuit Absorbant Accessible\n\n"
                "Ce graphe contient un circuit absorbant accessible depuis la source A.\n"
                "- Source : A\n"
                "- Circuit absorbant : B -> C -> D -> B de poids 3 + (-6) + 1 = -2 < 0.\n"
                "- Sommet E : accessible depuis D, donc sa distance depuis A est -infini.\n"
                "- Comportement attendu : Bellman-Ford et Floyd-Warshall doivent détecter le circuit absorbant,\n"
                "  indiquer qu'il est accessible depuis A, et refuser d'afficher une distance finie pour B, C, D, E.\n")


def generer_jeu_absorbant_non_accessible(base_dir="data/test_absorbant_non_accessible"):
    """Génère un graphe contenant un circuit absorbant NON accessible depuis la source A.

    Topologie :
    Composante 1 (accessible depuis A) :
    A (source) -> B (coût 4)
    B -> C (coût 2)
    A -> C (coût 7)
    Toutes les distances depuis A sont bien définies : dist(A)=0, dist(B)=4, dist(C)=6.

    Composante 2 (isolée de A, avec circuit absorbant) :
    X -> Y (coût 1)
    Y -> Z (coût 2)
    Z -> X (coût -5)   --> Circuit X -> Y -> Z -> X de poids 1 + 2 - 5 = -2 < 0 !
    Aucun chemin ne mène de {A, B, C} vers {X, Y, Z}.
    """
    creer_dossier_si_absent(base_dir)

    sites_entetes = ["id", "nom", "type", "longitude", "latitude"]
    sites_lignes = [
        ["A", "Source", "source", 0.0, 0.0],
        ["B", "Etape B", "noeud", 1.0, 0.0],
        ["C", "Destination C", "destination", 2.0, 0.0],
        ["X", "Cycle X", "cycle_isole", 10.0, 10.0],
        ["Y", "Cycle Y", "cycle_isole", 11.0, 11.0],
        ["Z", "Cycle Z", "cycle_isole", 10.0, 12.0],
    ]
    ecrire_csv(os.path.join(base_dir, "sites.csv"), sites_entetes, sites_lignes)

    routes_entetes = ["u", "v", "temps_normal", "temps_pointe", "statut", "type_voie", "capacite"]
    routes_lignes = [
        # Composante accessible depuis A
        ["A", "B", 4.0, 4.0, "ouvert", "route", 1000],
        ["B", "C", 2.0, 2.0, "ouvert", "route", 1000],
        ["A", "C", 7.0, 7.0, "ouvert", "route", 1000],
        # Composante avec circuit absorbant non accessible depuis A
        ["X", "Y", 1.0, 1.0, "ouvert", "cycle", 1000],
        ["Y", "Z", 2.0, 2.0, "ouvert", "cycle", 1000],
        ["Z", "X", -5.0, -5.0, "ouvert", "cycle", 1000],  # Somme = -2 < 0
    ]
    ecrire_csv(os.path.join(base_dir, "routes.csv"), routes_entetes, routes_lignes)

    fibre_entetes = ["u", "v", "cost", "statut"]
    fibre_lignes = [
        ["A", "B", 3.0, "actif"],
        ["B", "C", 3.0, "actif"],
    ]
    ecrire_csv(os.path.join(base_dir, "fibre.csv"), fibre_entetes, fibre_lignes)

    demandes_entetes = ["id", "origine", "destination", "type", "priorite"]
    demandes_lignes = [
        ["D_NON_ACC_1", "A", "C", "test_distance_valide", 1],
    ]
    ecrire_csv(os.path.join(base_dir, "demandes.csv"), demandes_entetes, demandes_lignes)

    scenarios_entetes = ["scenario_id", "type_element", "u", "v", "action", "valeur"]
    scenarios_lignes = [
        ["scenario_normal", "aucun", "none", "none", "baseline", "0"]
    ]
    ecrire_csv(os.path.join(base_dir, "scenarios.csv"), scenarios_entetes, scenarios_lignes)

    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Graphe de Test : Circuit Absorbant Non Accessible\n\n"
                "Ce graphe contient un circuit absorbant non accessible depuis la source A.\n"
                "- Source : A\n"
                "- Plus courts chemins depuis A : dist(A)=0, dist(B)=4, dist(C)=6 (chemin A->B->C).\n"
                "- Circuit absorbant : X -> Y -> Z -> X de poids 1 + 2 - 5 = -2 < 0.\n"
                "- Comportement attendu : Bellman-Ford lancé depuis A doit renvoyer les distances exactes pour A, B, C,\n"
                "  tout en signalant que le circuit absorbant n'impacte pas la source A. Floyd-Warshall détecte le cycle\n"
                "  sur sa diagonale pour X, Y, Z, mais conserve des distances finies entre A, B et C.\n")


def generer_tous_les_jeux(base_data_dir="data"):
    """Génère l'ensemble des 4 jeux de données avec affichage de la progression."""
    print("=" * 70)
    print("NOVAPOLIS RÉSILIENCE : GÉNÉRATION DES JEUX DE DONNÉES CSV")
    print("=" * 70)

    print("\n[1/4] Génération du jeu manuel (data/manuel)...")
    generer_jeu_manuel(os.path.join(base_data_dir, "manuel"))
    print("      -> 8 sites, vérifiable sur papier.")

    print("\n[2/4] Génération du jeu réaliste documenté (data/realiste)...")
    generer_jeu_realiste(os.path.join(base_data_dir, "realiste"), nb_sites=110, seed=42)
    print("      -> 110 sites, 5 districts, multi-scénarios.")

    print("\n[3/4] Génération du jeu synthétique d'échelle (data/synthetique)...")
    generer_jeu_synthetique(os.path.join(base_data_dir, "synthetique"), nb_sites=1000, seed=42)
    print("      -> 1000 sites, graine aléatoire fixée (seed 42).")

    print("\n[4/4] Génération des jeux de test pour circuits absorbants...")
    generer_jeu_absorbant_accessible(os.path.join(base_data_dir, "test_absorbant_accessible"))
    print("      -> data/test_absorbant_accessible (accessible depuis la source).")
    generer_jeu_absorbant_non_accessible(os.path.join(base_data_dir, "test_absorbant_non_accessible"))
    print("      -> data/test_absorbant_non_accessible (non accessible depuis la source).")

    print("\n" + "=" * 70)
    print("GÉNÉRATION TERMINÉE AVEC SUCCÈS POUR TOUS LES JEUX DE DONNÉES !")
    print("=" * 70)


if __name__ == "__main__":
    generer_tous_les_jeux()
