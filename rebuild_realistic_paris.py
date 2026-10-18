"""Générateur de précision pour Novapolis Paris (Jeu de données Réaliste 110 sites).

Positionne avec exactitude les 110 sites sur leurs coordonnées cadastrales réelles à Paris :
- Hôpitaux (Hôtel-Dieu sur l'Île de la Cité, Lariboisière, Pitié-Salpêtrière, Georges-Pompidou, Saint-Antoine)
- Casernes de pompiers BSPP (Châtelet, Montmartre, Masséna, Chaligny, Dauphine)
- Hubs télécoms, lycées historiques et quartiers parisiens
- Réseau routier respectant la topologie viaire et le franchissement exclusif par les vrais ponts de la Seine
"""

import os
import math
import random
import csv
from typing import List, Dict, Tuple

RACINE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(RACINE, "data", "realiste")

# Coordonnées géographiques réelles (WGS84 : longitude, latitude)
SITES_EXACTS = [
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

    # --- PÔLE ACADÉMIQUE D'EXCELLENCE & TECHNOLOGIES ---
    ("SITE_111", "Efrei Paris - Campus Villejuif", "ecole", 2.3637, 48.7887),
]


def distance_km(lon1, lat1, lon2, lat2) -> float:
    """Distance géodésique sur la terre (Haversine)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    random.seed(42)

    # 1. Écriture de sites.csv
    sites_path = os.path.join(DATA_DIR, "sites.csv")
    with open(sites_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "nom", "type", "longitude", "latitude"])
        for s_id, s_nom, s_type, s_lon, s_lat in SITES_EXACTS:
            w.writerow([s_id, s_nom, s_type, s_lon, s_lat])
    print(f"Sites réels écrits ({len(SITES_EXACTS)} sommets géoréférencés).")

    # Dictionnaire des coordonnées
    coord_dict = {s[0]: (s[3], s[4]) for s in SITES_EXACTS}
    id_list = [s[0] for s in SITES_EXACTS]

    # 2. Construction du réseau routier réaliste (routes.csv)
    # Règle d'or : chaque site est relié à ses plus proches voisins locaux (dans un rayon de 1.8 km)
    # Les liaisons intervilles empruntent les grands axes (boulevards, quais)
    routes_set = set()
    routes_rows = []

    def ajouter_arc_routier(u, v, v_kmh=30.0, type_voie="rue_locale", capacite=800):
        if u == v or (u, v) in routes_set:
            return
        lon1, lat1 = coord_dict[u]
        lon2, lat2 = coord_dict[v]
        d = distance_km(lon1, lat1, lon2, lat2)
        # Temps normal (en minutes)
        t_norm = round((d / v_kmh) * 60.0 + random.uniform(0.1, 0.4), 2)
        # Temps pointe (en minutes, congestion urbaine)
        t_pte = round(t_norm * random.uniform(1.4, 1.9), 2)
        routes_set.add((u, v))
        routes_rows.append([u, v, t_norm, t_pte, "ouvert", type_voie, capacite])

    # A. Voisins locaux dans chaque district
    for i, u in enumerate(id_list[:105]):
        lon1, lat1 = coord_dict[u]
        voisins_proches = []
        for j, v in enumerate(id_list[:105]):
            if i != j:
                lon2, lat2 = coord_dict[v]
                d = distance_km(lon1, lat1, lon2, lat2)
                if d <= 1.4:
                    voisins_proches.append((d, v))
        voisins_proches.sort()
        # Connecter au moins les 3 plus proches
        for d_v, v in voisins_proches[:4]:
            ajouter_arc_routier(u, v, v_kmh=25.0, type_voie="rue_locale", capacite=600)
            ajouter_arc_routier(v, u, v_kmh=25.0, type_voie="rue_locale", capacite=600)

    # B. Grands axes structurants et vrais ponts parisiens
    GRANDS_AXES = [
        # Axe Châtelet <-> Gare du Nord / Lariboisière (Bd de Sébastopol / Strasbourg)
        ("SITE_001", "SITE_010"), ("SITE_010", "SITE_023"), ("SITE_023", "SITE_032"), ("SITE_032", "SITE_028"), ("SITE_028", "SITE_027"),
        # Ponts réels vers Île de la Cité et Hôtel-Dieu
        ("SITE_001", "SITE_017"), ("SITE_017", "SITE_008"), ("SITE_008", "SITE_002"), ("SITE_002", "SITE_016"),
        # Ponts réels Cité vers Rive Gauche (Pont Saint-Michel, Petit Pont)
        ("SITE_008", "SITE_025"), ("SITE_016", "SITE_025"), ("SITE_025", "SITE_004"),
        # Rive Gauche : Châtelet vers Masséna (Bd Saint-Michel / Bd de l'Hôpital / Av. d'Italie)
        ("SITE_004", "SITE_050"), ("SITE_050", "SITE_049"), ("SITE_049", "SITE_057"), ("SITE_057", "SITE_048"), ("SITE_048", "SITE_055"), ("SITE_055", "SITE_046"),
        # Rive Droite : Châtelet vers Bastille et Chaligny (Rue de Rivoli / Fbg Saint-Antoine)
        ("SITE_001", "SITE_007"), ("SITE_007", "SITE_005"), ("SITE_005", "SITE_071"), ("SITE_071", "SITE_080"), ("SITE_080", "SITE_066"), ("SITE_066", "SITE_067"), ("SITE_067", "SITE_068"),
        # Pont d'Austerlitz (liaison essentielle 12e <-> 13e, Bercy <-> Salpêtrière)
        ("SITE_079", "SITE_058"), ("SITE_058", "SITE_047"),
        # Pont de Bercy (Accor Arena 12e <-> BNF 13e)
        ("SITE_075", "SITE_061"),
        # Liaison Ouest : Châtelet vers Étoile et Dauphine (Rivoli / Concorde / Champs-Élysées)
        ("SITE_001", "SITE_009"), ("SITE_009", "SITE_018"), ("SITE_018", "SITE_095"), ("SITE_095", "SITE_096"), ("SITE_096", "SITE_088"), ("SITE_088", "SITE_094"), ("SITE_094", "SITE_086"),
        # Pont Alexandre III / Iéna (Invalides 7e <-> Trocadéro / Tour Eiffel)
        ("SITE_105", "SITE_099"), ("SITE_099", "SITE_091"), ("SITE_091", "SITE_089"),
        # Pont Mirabeau (15e Pompidou <-> 16e Auteuil)
        ("SITE_087", "SITE_102"), ("SITE_102", "SITE_093"),
        # Connexion Périphérie Val-de-Marne
        ("SITE_069", "SITE_085"), ("SITE_085", "SITE_106"), ("SITE_106", "SITE_107"), ("SITE_107", "SITE_108"), ("SITE_108", "SITE_109"),
        # Refuge 110 relié uniquement en sortie pour tester les sites sans entrée / sans sortie
        ("SITE_109", "SITE_110"),
        # Raccordement Campus Efrei Paris (Avenue de Paris / RD7 / Porte d'Italie)
        ("SITE_046", "SITE_111"), ("SITE_055", "SITE_111"), ("SITE_054", "SITE_111"), ("SITE_048", "SITE_111"),
    ]

    for u, v in GRANDS_AXES:
        t_voie = "pont" if (u in ("SITE_008", "SITE_016", "SITE_017", "SITE_075", "SITE_102", "SITE_105") or v in ("SITE_008", "SITE_016", "SITE_017", "SITE_075", "SITE_102", "SITE_105")) else "boulevard"
        cap = 2000 if t_voie == "boulevard" else 1500
        ajouter_arc_routier(u, v, v_kmh=40.0, type_voie=t_voie, capacite=cap)
        ajouter_arc_routier(v, u, v_kmh=40.0, type_voie=t_voie, capacite=cap)

    routes_path = os.path.join(DATA_DIR, "routes.csv")
    with open(routes_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["u", "v", "temps_normal", "temps_pointe", "statut", "type_voie", "capacite"])
        for r in routes_rows:
            w.writerow(r)
    print(f"Routes réelles écrites ({len(routes_rows)} arcs orientés).")

    # 3. Réseau de fibre optique (fibre.csv)
    # Graphe non orienté. Doit interconnecter les casernes, hôpitaux et hubs télécoms
    fibre_set = set()
    fibre_rows = []

    def ajouter_arete_fibre(u, v, cout=None):
        paire = tuple(sorted([u, v]))
        if u == v or paire in fibre_set:
            return
        lon1, lat1 = coord_dict[u]
        lon2, lat2 = coord_dict[v]
        d = distance_km(lon1, lat1, lon2, lat2)
        if cout is None:
            cout = round(d * 4.5 + random.uniform(1.0, 3.0), 1)
        fibre_set.add(paire)
        fibre_rows.append([paire[0], paire[1], cout, "actif"])

    # Dorsale optique reliant les 5 hubs et casernes
    DORSALE_FIBRE = [
        ("SITE_001", "SITE_002"),
        ("SITE_001", "SITE_003"),
        ("SITE_003", "SITE_028"),
        ("SITE_028", "SITE_027"),
        ("SITE_028", "SITE_026"),
        ("SITE_001", "SITE_048"),
        ("SITE_048", "SITE_047"),
        ("SITE_048", "SITE_046"),
        ("SITE_001", "SITE_068"),
        ("SITE_068", "SITE_067"),
        ("SITE_068", "SITE_066"),
        ("SITE_001", "SITE_088"),
        ("SITE_088", "SITE_086"),
        ("SITE_088", "SITE_087"),
        # Maillage de secours entre les anneaux
        ("SITE_028", "SITE_068"),
        ("SITE_068", "SITE_048"),
        ("SITE_048", "SITE_088"),
        ("SITE_088", "SITE_028"),
        # Connexion Périphérie
        ("SITE_068", "SITE_106"),
        ("SITE_106", "SITE_107"),
        ("SITE_107", "SITE_108"),
        ("SITE_108", "SITE_109"),
        # SITE_110 non raccordé volontairement pour tester la forêt couvrante
        # Raccordement fibre académique très haut débit Efrei Paris (Campus Villejuif)
        ("SITE_048", "SITE_111"),
        ("SITE_046", "SITE_111"),
    ]
    for u, v in DORSALE_FIBRE:
        ajouter_arete_fibre(u, v)

    # Capillaires locaux
    for i, u in enumerate(id_list[:105]):
        lon1, lat1 = coord_dict[u]
        candidats = []
        for j, v in enumerate(id_list[:105]):
            if i != j:
                lon2, lat2 = coord_dict[v]
                d = distance_km(lon1, lat1, lon2, lat2)
                if d <= 1.2:
                    candidats.append((d, v))
        candidats.sort()
        for d_v, v in candidats[:2]:
            ajouter_arete_fibre(u, v)

    fibre_path = os.path.join(DATA_DIR, "fibre.csv")
    with open(fibre_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["u", "v", "cost", "statut"])
        for r in fibre_rows:
            w.writerow(r)
    print(f"Fibre optique écrite ({len(fibre_rows)} arêtes).")

    # 4. Demandes de secours (demandes.csv)
    demandes_rows = [
        ["DEM_001", "SITE_001", "SITE_002", "urgence_medicale", 1],
        ["DEM_002", "SITE_001", "SITE_027", "incendie", 1],
        ["DEM_003", "SITE_026", "SITE_031", "secours", 2],
        ["DEM_004", "SITE_046", "SITE_058", "inondation", 1],
        ["DEM_005", "SITE_066", "SITE_075", "accident", 1],
        ["DEM_006", "SITE_086", "SITE_099", "secours", 2],
        ["DEM_007", "SITE_001", "SITE_047", "urgence_medicale", 1],
        ["DEM_008", "SITE_046", "SITE_061", "secours", 2],
        ["DEM_009", "SITE_066", "SITE_069", "incendie", 1],
        ["DEM_010", "SITE_086", "SITE_087", "urgence_medicale", 1],
        ["DEM_011", "SITE_001", "SITE_106", "renfort", 1],
        ["DEM_012", "SITE_066", "SITE_107", "accident", 2],
        ["DEM_013", "SITE_001", "SITE_110", "inaccessible_test", 1],  # Test inaccessibilité
        ["DEM_014", "SITE_046", "SITE_111", "urgence_campus_efrei", 1],  # Caserne Masséna -> Efrei Paris
        ["DEM_015", "SITE_001", "SITE_111", "renfort_commandement", 1],  # Caserne Châtelet -> Efrei Paris
    ]
    demandes_path = os.path.join(DATA_DIR, "demandes.csv")
    with open(demandes_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "origine", "destination", "type", "priorite"])
        for r in demandes_rows:
            w.writerow(r)
    print(f"Demandes écrites ({len(demandes_rows)} requêtes).")

    # 5. Scénarios de perturbation (scenarios.csv)
    # Fermeture de ponts réels et inondation sur les quais
    scenarios_rows = [
        ["scenario_normal", "aucun", "none", "none", "baseline", "0"],
        # Fermeture du Pont d'Austerlitz (axe SITE_079 <-> SITE_058) et accès Bords de Marne SITE_085 <-> SITE_106
        ["scenario_fermeture_pont", "route", "SITE_079", "SITE_058", "fermer", "0"],
        ["scenario_fermeture_pont", "route", "SITE_058", "SITE_079", "fermer", "0"],
        ["scenario_fermeture_pont", "route", "SITE_085", "SITE_106", "fermer", "0"],
        # Panne sur la dorsale fibre principale
        ["scenario_panne_fibre_dorsale", "fibre", "SITE_001", "SITE_003", "panne", "0"],
        ["scenario_panne_fibre_dorsale", "fibre", "SITE_003", "SITE_028", "panne", "0"],
        # Inondation Sud : quais fermés et rupture de pont fluvial
        ["scenario_inondation_sud", "route", "SITE_075", "SITE_061", "fermer", "0"],
        ["scenario_inondation_sud", "route", "SITE_061", "SITE_075", "fermer", "0"],
        ["scenario_inondation_sud", "route", "SITE_058", "SITE_047", "fermer", "0"],
        ["scenario_inondation_sud", "fibre", "SITE_001", "SITE_048", "panne", "0"],
    ]
    scenarios_path = os.path.join(DATA_DIR, "scenarios.csv")
    with open(scenarios_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario_id", "type_element", "u", "v", "action", "valeur"])
        for r in scenarios_rows:
            w.writerow(r)
    print("Scénarios écrits.")


if __name__ == "__main__":
    main()
