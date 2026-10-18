import csv
import random

def generer_jeu_de_donnees(nb_sites, prefix=""):
    """
    Génère les fichiers CSV pour le réseau routier et fibre.
    """
    types_sites = ['Caserne', 'Hopital', 'Quartier', 'Ecole', 'Telecom']
    
    # 1. Génération de sites.csv
    sites = []
    for id_site in range(1, nb_sites + 1):
        # Répartition arbitraire : beaucoup de quartiers, peu de casernes/hôpitaux
        type_site = random.choices(types_sites, weights=[5, 5, 70, 10, 10])[0]
        sites.append({
            'id': id_site,
            'nom': f"{type_site}_{id_site}",
            'type': type_site,
            # Coordonnées fictives (autour de Paris/Novapolis par ex)
            'longitude': round(random.uniform(2.0, 2.5), 4),
            'latitude': round(random.uniform(48.5, 49.0), 4)
        })
        
    with open(f'{prefix}sites.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'nom', 'type', 'longitude', 'latitude'])
        writer.writeheader()
        writer.writerows(sites)

    # 2. Génération de routes.csv (Graphe orienté)
    routes = []
    for u in range(1, nb_sites + 1):
        # Chaque site a entre 2 et 5 routes sortantes
        nb_voisins = random.randint(2, 5)
        voisins = random.sample(range(1, nb_sites + 1), min(nb_voisins, nb_sites - 1))
        
        for v in voisins:
            if u != v:
                temps_norm = random.randint(5, 30)
                routes.append({
                    'u': u,
                    'v': v,
                    'temps_normal': temps_norm,
                    'temps_pointe': temps_norm + random.randint(5, 20),
                    'statut': 'ouvert'
                })

    with open(f'{prefix}routes.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['u', 'v', 'temps_normal', 'temps_pointe', 'statut'])
        writer.writeheader()
        writer.writerows(routes)

    # 3. Génération de fibre.csv (Graphe non orienté)
    fibre = []
    # Pour s'assurer que le graphe de la fibre a une chance d'être connexe, 
    # on relie au moins chaque noeud i au noeud i+1
    for i in range(1, nb_sites):
        fibre.append({'u': i, 'v': i + 1, 'cost': random.randint(100, 1000), 'statut': 'disponible'})
    
    # Ajout d'arêtes aléatoires supplémentaires pour la redondance
    for _ in range(nb_sites):
        u, v = random.sample(range(1, nb_sites + 1), 2)
        fibre.append({'u': u, 'v': v, 'cost': random.randint(100, 1000), 'statut': 'disponible'})

    with open(f'{prefix}fibre.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['u', 'v', 'cost', 'statut'])
        writer.writeheader()
        writer.writerows(fibre)
        
    print(f"Jeux de données '{prefix}' générés avec succès pour {nb_sites} sites !")

# Générer les 3 jeux demandés par le projet
if __name__ == "__main__":
    generer_jeu_de_donnees(10, prefix="petit_")     # Pour vérifier à la main
    generer_jeu_de_donnees(150, prefix="moyen_")    # Jeu réaliste
    generer_jeu_de_donnees(1000, prefix="grand_")   # Jeu généré imposé (1000+ sommets)