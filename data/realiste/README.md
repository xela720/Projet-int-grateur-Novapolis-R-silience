# Jeu de Données Réaliste Documenté : Novapolis Métropole (110 sites)

Ce jeu de données modélise une métropole complète avec ses infrastructures critiques.

## Structure du réseau
- **Sites (110)** : 5 casernes de pompiers, 5 hôpitaux, 5 hubs télécom, 10 écoles, 80 quartiers, 4 sites logistiques, 1 site isolé de colline.
- **Districts (5)** : Centre, Nord, Sud, Est, Ouest, et zone périphérique.
- **Réseau routier** : Réseau dirigé réaliste comprenant un boulevard périphérique, des radiales et des rues locales (avec temps normal et de pointe).
- **Réseau fibre** : Dorsale optique en anneau à haute disponibilité reliant les sites critiques, complétée par un maillage capillaire.
- **Scénarios testés** :
  1. `scenario_normal` : Situation fluide nominale.
  2. `scenario_fermeture_pont` : Rupture de l'axe vers la presqu'île (hausse brutale du temps d'intervention / enclavement).
  3. `scenario_panne_fibre_dorsale` : Rupture d'un tronçon critique de fibre optique (évaluation du coût de re-routage MST).
  4. `scenario_inondation_sud` : Crise multi-réseaux (coupure de routes et de fibres simultanées).
