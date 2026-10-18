"""Tableau de bord Web Novapolis Résilience — Version Éditoriale & Cartographique Paris.

Conforme aux directives de design sobre, typographique et utilitaire (anti-AI slop, zero emoji).
Intègre la cartographie réelle de Paris avec support multi-fonds :
- CartoDB Dark Matter & Positron
- Google Maps Platform (Plan & Satellite Hybride)

Fonctionnalités interactives en direct (100% Python standard, zéro NetworkX) :
1. Calculs d'itinéraires d'urgence par Dijkstra avec télémétrie étape par étape.
2. Déploiement et visualisation de l'arbre couvrant minimal de fibre optique (Kruskal / Prim).
3. Simulateur interactif de panne de câble et calcul du raccordement de secours optimal.
4. Matrice comparative de résilience multiscénario en temps réel (Module 5).
"""

import os
import sys
import math
import json
import http.server
import socketserver
import urllib.parse
from typing import Dict, Any

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from src.data_manager import charger_reseau, appliquer_scenario
from src.shortest_paths import dijkstra, reconstruire_chemin
from src.spanning_tree import kruskal, simuler_panne_troncon
from src.accessibility import diagnostic_accessibilite
from src.resilience import comparer_tous_les_scenarios

PORT_DEFAUT = 8000
_CACHE_RESEAUX = {}


def obtenir_reseau_base(dossier_data: str):
    """Retourne le réseau depuis le cache mémoire pour des réponses API instantanées."""
    if dossier_data not in _CACHE_RESEAUX:
        _CACHE_RESEAUX[dossier_data] = charger_reseau(dossier_data)
    return _CACHE_RESEAUX[dossier_data]


def preparer_donnees_json(dossier_data: str, scenario_id: str, poids: str = "temps_normal") -> Dict[str, Any]:
    """Exécute les calculs de graphes et prépare le payload JSON pour l'interface web."""
    reseau_base = obtenir_reseau_base(dossier_data)
    reseau_pert = appliquer_scenario(reseau_base, scenario_id)

    # 1. Sites
    sites_dict = {}
    for s_id, s in reseau_base.routier.sites.items():
        sites_dict[s_id] = {
            "id": s.id,
            "nom": s.nom,
            "type": s.type,
            "lat": s.latitude,
            "lng": s.longitude,
        }

    # 2. Routes et statuts
    routes_liste = []
    for arc in reseau_base.routier.tous_les_arcs():
        arc_pert = reseau_pert.routier.adj.get(arc.u, {}).get(arc.v)
        est_ouvert = arc_pert.est_ouvert() if arc_pert else False
        routes_liste.append({
            "u": arc.u,
            "v": arc.v,
            "temps": arc.temps_normal,
            "temps_pointe": arc.temps_pointe,
            "ouvert": est_ouvert,
        })

    # 3. Fibre et MST
    mst_res = kruskal(reseau_pert.fibre)
    mst_aretes = [list(a.extremites()) for a in mst_res["aretes"]]

    # 4. Diagnostic d'accessibilité
    diag = diagnostic_accessibilite(reseau_pert.routier, reseau_pert.fibre)

    # 5. Synthèse multiscénario pour la matrice de résilience
    matrice_brute = comparer_tous_les_scenarios(reseau_base, poids=poids)
    matrice_clean = {}
    for sc_k, sc_v in matrice_brute.items():
        matrice_clean[sc_k] = {
            "demandes_perdues": sc_v["demandes_devenues_inaccessibles"],
            "pourcentage_perdues": sc_v["pourcentage_demandes_perdues"],
            "retard_moyen": sc_v["hausse_moyenne_temps_min"],
            "retard_max": sc_v["hausse_maximale_temps_min"],
            "sensibles_pct": round(sc_v["proportion_sensibles_accessibles"] * 100, 1),
            "composantes_fibre": sc_v["nb_composantes_fibre_pert"],
            "cout_reparation": sc_v["cout_reparation_estime"],
        }

    return {
        "dataset": dossier_data,
        "scenario": scenario_id,
        "scenarios_disponibles": list(reseau_base.scenarios.keys()),
        "sites": sites_dict,
        "routes": routes_liste,
        "mst_fibre": mst_aretes,
        "cout_mst": mst_res["cout_total"],
        "diagnostic": {
            "taux_acces": round(diag["taux_accessibilite_globale"] * 100, 1),
            "sensibles_couverts": f"{diag['nb_sensibles_accessibles']}/{diag['nb_sites_sensibles']}",
            "comp_fibre": diag["nb_composantes_fibre"],
        },
        "matrice_resilience": matrice_clean,
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novapolis Paris — Centre de Supervision & Résilience Métropolitaine</title>
    <!-- Google Fonts: Plus Jakarta Sans & JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {
            --bg-canvas: #06080d;
            --bg-sidebar: #0a0e17;
            --bg-subtle: #0f1522;
            --bg-card: #121927;
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.16);
            --border-focus: #0ea5e9;

            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;

            --accent-emerald: #10b981;
            --accent-emerald-subtle: rgba(16, 185, 129, 0.18);
            --accent-red: #f43f5e;
            --accent-red-subtle: rgba(244, 63, 94, 0.18);
            --accent-cyan: #0ea5e9;
            --accent-amber: #f59e0b;
            --accent-indigo: #6366f1;
            --accent-indigo-subtle: rgba(99, 102, 241, 0.18);

            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, monospace;
            --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            display: flex;
            height: 100vh;
            background: var(--bg-canvas);
            color: var(--text-primary);
            font-family: var(--font-sans);
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Sidebar navigation et commandes */
        #sidebar {
            width: 420px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            padding: 24px 20px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 12px 0 36px rgba(0, 0, 0, 0.4);
        }
        #sidebar > * { flex-shrink: 0; }
        #sidebar::-webkit-scrollbar { width: 4px; }
        #sidebar::-webkit-scrollbar-track { background: transparent; }
        #sidebar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 2px; }
        #sidebar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.22); }

        .brand-block {
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 16px;
        }
        .status-beacon-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.22);
            padding: 3px 9px;
            border-radius: 9999px;
            margin-bottom: 10px;
        }
        .beacon-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent-emerald);
            flex-shrink: 0;
        }
        .beacon-text {
            font-family: var(--font-mono);
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            color: var(--accent-emerald);
        }
        .brand-title {
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.035em;
            color: var(--text-primary);
        }
        .brand-meta {
            font-size: 0.77rem;
            color: var(--text-secondary);
            margin-top: 4px;
            line-height: 1.45;
        }

        /* Hero Card Démo Efrei Paris (Clean Solid Architecture) */
        .efrei-hero-card {
            background: #0f1522;
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 16px;
        }
        .efrei-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .efrei-badge {
            font-size: 0.64rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #93c5fd;
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.25);
            padding: 2px 7px;
            border-radius: 4px;
            white-space: nowrap;
        }
        .efrei-code {
            font-family: var(--font-mono);
            font-size: 0.70rem;
            font-weight: 600;
            color: var(--text-muted);
            white-space: nowrap;
        }
        .efrei-title {
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        .efrei-desc {
            font-size: 0.73rem;
            color: var(--text-secondary);
            line-height: 1.4;
            margin-bottom: 10px;
        }
        .btn-efrei {
            width: 100%;
            background: #1a2233;
            color: #f1f5f9;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: background-color 0.15s ease, border-color 0.15s ease;
        }
        .btn-efrei:hover {
            background: #243047;
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.2);
        }
        .btn-efrei:active {
            transform: translateY(1px);
        }
        .btn-efrei-arrow {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .section-heading {
            font-size: 0.67rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin: 18px 0 8px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-heading::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255, 255, 255, 0.06);
        }

        label {
            font-size: 0.77rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 5px;
            display: block;
        }

        select {
            width: 100%;
            padding: 9px 32px 9px 12px;
            background-color: #0f1522;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 0.82rem;
            margin-bottom: 12px;
            outline: none;
            cursor: pointer;
            appearance: none;
            -webkit-appearance: none;
            transition: all 0.15s var(--ease-spring);
        }
        select:hover {
            border-color: var(--border-hover);
        }
        select:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
        }

        .btn-primary {
            width: 100%;
            background: #2563eb;
            color: #ffffff;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.84rem;
            letter-spacing: -0.01em;
            padding: 10px 14px;
            cursor: pointer;
            margin-top: 4px;
            margin-bottom: 8px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-primary:hover {
            background: #1d4ed8;
            border-color: #2563eb;
        }
        .btn-primary:active {
            transform: translateY(1px);
        }

        .btn-secondary {
            width: 100%;
            background: #131926;
            color: var(--text-secondary);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            font-weight: 500;
            font-size: 0.80rem;
            padding: 9px 12px;
            cursor: pointer;
            margin-bottom: 10px;
            transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }
        .btn-secondary:hover {
            background: #1a2233;
            border-color: var(--border-hover);
            color: var(--text-primary);
        }
        .btn-secondary:active {
            transform: translateY(1px);
        }

        /* Cartes télémétriques */
        .telemetry-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 14px;
        }
        .metric-cell {
            background: #0f1522;
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 10px 12px;
            transition: border-color 0.15s ease;
        }
        .metric-cell:hover {
            border-color: var(--border-hover);
        }
        .metric-inner {
            background: transparent;
        }
        .metric-label {
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }
        .metric-value {
            font-family: var(--font-mono);
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-top: 3px;
            letter-spacing: -0.02em;
            font-variant-numeric: tabular-nums;
        }
        .metric-value.status-alert { color: var(--accent-red); }
        .metric-value.status-ok { color: var(--accent-emerald); }

        /* Journal d'itinéraire de secours */
        #itinerary-log {
            background: rgba(14, 20, 32, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 10px;
            padding: 13px 14px;
            margin-top: 10px;
            margin-bottom: 16px;
            max-height: 220px;
            overflow-y: auto;
            display: none;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            flex-shrink: 0;
        }
        #itinerary-log::-webkit-scrollbar { width: 4px; }
        #itinerary-log::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 2px; }

        .itinerary-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--border-subtle);
        }
        .itinerary-title {
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
        }
        .itinerary-badge {
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--accent-emerald);
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.28);
            padding: 2px 8px;
            border-radius: 5px;
        }
        .itinerary-timeline {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .itinerary-step {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            position: relative;
        }
        .step-indicator {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 12px;
            flex-shrink: 0;
            padding-top: 4px;
        }
        .step-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .step-line {
            width: 1px;
            flex: 1;
            min-height: 18px;
            background: var(--border-subtle);
            margin: 2px 0;
        }
        .step-content {
            flex: 1;
            min-width: 0;
            padding-bottom: 6px;
        }
        .step-top {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 6px;
        }
        .step-name {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .step-id {
            font-family: var(--font-mono);
            font-size: 0.70rem;
            color: var(--text-muted);
            flex-shrink: 0;
        }
        .step-role {
            font-size: 0.70rem;
            color: var(--text-secondary);
            margin-top: 1px;
        }

        /* Conteneur principal Carte */
        #map-container {
            flex: 1;
            position: relative;
            height: 100vh;
            background: #07090e;
        }
        #leaflet-map { width: 100%; height: 100%; }

        /* Contrôles HUD supérieurs (Floating Glass Dock) */
        #hud-controls {
            position: absolute;
            top: 18px;
            right: 20px;
            z-index: 999;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: #0d121d;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            padding: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
        }
        .hud-divider {
            width: 1px;
            height: 18px;
            background: rgba(255, 255, 255, 0.1);
            margin: 0 3px;
        }
        #select-basemap {
            background-color: #161e2e;
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: #f1f5f9;
            font-size: 0.77rem;
            font-weight: 600;
            padding: 6px 28px 6px 10px;
            margin-bottom: 0;
            width: auto;
            border-radius: 6px;
            cursor: pointer;
            outline: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 8px center;
            appearance: none;
            -webkit-appearance: none;
            transition: background-color 0.15s ease, border-color 0.15s ease;
        }
        #select-basemap:hover {
            border-color: rgba(255, 255, 255, 0.25);
            background-color: #1c273a;
        }
        .hud-toggle {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            padding: 6px 11px;
            border-radius: 6px;
            font-size: 0.77rem;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.12s ease, color 0.12s ease, border-color 0.12s ease;
            white-space: nowrap;
        }
        .hud-toggle:hover {
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-primary);
        }
        .hud-toggle.active {
            background: #26334d;
            color: #ffffff;
            font-weight: 600;
            border-color: #3b82f6;
        }
        .hud-toggle-efrei {
            background: rgba(59, 130, 246, 0.12) !important;
            border: 1px solid rgba(59, 130, 246, 0.3) !important;
            color: #93c5fd !important;
            font-weight: 600 !important;
        }
        .hud-toggle-efrei:hover {
            background: #2563eb !important;
            color: #ffffff !important;
            border-color: #2563eb !important;
        }

        /* Légende cartographique épurée */
        #legend {
            position: absolute;
            bottom: 24px;
            right: 24px;
            background: #0d121d;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            padding: 14px 16px;
            font-size: 0.75rem;
            z-index: 999;
            min-width: 210px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        .legend-header {
            font-size: 0.67rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 9px;
            margin-bottom: 6px;
            color: var(--text-secondary);
            font-size: 0.74rem;
        }
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .line-swatch {
            width: 14px;
            height: 2px;
            border-radius: 1px;
            flex-shrink: 0;
        }

        /* Modal Matrice de Résilience (Doppelrand) */
        #matrix-modal {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(4, 6, 10, 0.82);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        .modal-card {
            background: #0d121e;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            width: 800px;
            max-width: 90vw;
            padding: 24px 26px;
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.65);
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-subtle);
        }
        .modal-close {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-secondary);
            font-size: 1.1rem;
            cursor: pointer;
            width: 30px;
            height: 30px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
        }
        .modal-close:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }
        .matrix-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
            text-align: left;
        }
        .matrix-table th {
            padding: 9px 12px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-subtle);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.68rem;
            letter-spacing: 0.05em;
        }
        .matrix-table td {
            padding: 11px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-family: var(--font-mono);
            font-size: 0.78rem;
        }
        .matrix-table tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        /* Leaflet Controls Styling */
        .leaflet-control-zoom {
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45) !important;
        }
        .leaflet-control-zoom a {
            background: rgba(11, 15, 24, 0.92) !important;
            color: var(--text-primary) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
            transition: background 0.15s ease;
        }
        .leaflet-control-zoom a:hover {
            background: rgba(255, 255, 255, 0.15) !important;
        }
    </style>
</head>
<body>

<div id="sidebar">
    <div class="brand-block">
        <div class="status-beacon-pill">
            <span class="beacon-dot"></span>
            <span class="beacon-text">SYSTÈME OPÉRATIONNEL • 111 SITES</span>
        </div>
        <div class="brand-title">Novapolis Paris</div>
        <div class="brand-meta">Supervision algorithmique des réseaux urbains & résilience de crise métropolitaine.</div>
    </div>

    <!-- SITE PRIORITAIRE : CAMPUS EFREI (Double-Bezel) -->
    <div class="efrei-hero-card">
        <div class="efrei-core">
            <div class="efrei-header">
                <span class="efrei-badge">CAMPUS SUPÉRIEUR • VILLEJUIF</span>
                <span class="efrei-code">SITE_111</span>
            </div>
            <div class="efrei-title">Intervention Rapide : Campus Efrei</div>
            <div class="efrei-desc">Départ d'urgence préconfiguré depuis la Caserne Masséna (13e) vers le campus de Villejuif (Avenue de Paris / RN7).</div>
            <button class="btn-efrei" onclick="lancerDemoEfrei()">
                <span>Calculer l'itinéraire vers l'Efrei</span>
                <span class="btn-efrei-arrow">➔</span>
            </button>
        </div>
    </div>

    <div class="section-heading">Configuration</div>
    <label for="select-dataset">Jeu de données :</label>
    <select id="select-dataset" onchange="changerEnvironnement()">
        <option value="data/realiste" selected>Novapolis Métropole (111 sites — Paris & Efrei)</option>
        <option value="data/manuel">Vérification Manuelle (8 sites)</option>
        <option value="data/synthetique">Jeu Synthétique Haute Échelle (1000 sites)</option>
        <option value="data/test_absorbant_accessible">Circuit Absorbant Accessible</option>
        <option value="data/test_absorbant_non_accessible">Circuit Absorbant Non Accessible</option>
    </select>

    <label for="select-scenario">Scénario de crise :</label>
    <select id="select-scenario" onchange="changerScenario()">
        <option value="scenario_normal">Situation nominale (Référence)</option>
    </select>

    <div class="section-heading">Itinéraires des Secours (Dijkstra)</div>
    <label for="select-depart">Caserne d'origine :</label>
    <select id="select-depart"></select>

    <label for="select-arrivee">Site cible d'intervention :</label>
    <select id="select-arrivee"></select>

    <button class="btn-primary" onclick="calculerItineraireDijkstra()">Calculer l'itinéraire d'urgence</button>
    <div id="itinerary-log"></div>

    <div class="section-heading">Indicateurs Opérationnels</div>
    <div class="telemetry-grid">
        <div class="metric-cell">
            <div class="metric-inner">
                <div class="metric-label">Durée trajet</div>
                <div id="kpi-temps" class="metric-value">—</div>
            </div>
        </div>
        <div class="metric-cell">
            <div class="metric-inner">
                <div class="metric-label">Retard crise</div>
                <div id="kpi-retard" class="metric-value status-ok">+0.0 min</div>
            </div>
        </div>
        <div class="metric-cell">
            <div class="metric-inner">
                <div class="metric-label">Sites sensibles</div>
                <div id="kpi-sensibles" class="metric-value">—</div>
            </div>
        </div>
        <div class="metric-cell">
            <div class="metric-inner">
                <div class="metric-label">Arbre Fibre (MST)</div>
                <div id="kpi-fibre" class="metric-value">—</div>
            </div>
        </div>
    </div>

    <div class="section-heading">Résilience Fibre (Coupure & Secours)</div>
    <label for="select-cable-cut">Tronçon d'arbre à rompre :</label>
    <select id="select-cable-cut"></select>
    <button class="btn-secondary" onclick="simulerCoupureCable()">Simuler rupture et calculer câble de secours</button>

    <button class="btn-secondary" style="margin-top: 6px;" onclick="ouvrirMatriceResilience()">Consulter la matrice de résilience multiscénario</button>
</div>

<div id="map-container">
    <div id="hud-controls">
        <select id="select-basemap" onchange="changerFondCarto()">
            <option value="esri_dark" selected>Plan Sombre (ESRI)</option>
            <option value="google_roadmap">Google Maps (Plan)</option>
            <option value="google_hybrid">Google Maps (Satellite)</option>
            <option value="osm_standard">OpenStreetMap</option>
        </select>
        <div class="hud-divider"></div>
        <button id="btn-voirie" class="hud-toggle active" onclick="toggleVoirie()">Voirie réelle</button>
        <button id="btn-routes" class="hud-toggle" onclick="toggleRoutesGraphe()">Arcs graphe</button>
        <button id="btn-fibre" class="hud-toggle active" onclick="toggleFibre()">Fibre (MST)</button>
        <button id="btn-pointe" class="hud-toggle" onclick="togglePointe()">Heure de pointe</button>
        <div class="hud-divider"></div>
        <button class="hud-toggle" onclick="recentrerVueParis()">Recentrer</button>
        <button class="hud-toggle hud-toggle-efrei" onclick="centrerSurEfrei()">Campus Efrei</button>
    </div>

    <div id="legend">
        <div class="legend-header">Légende Typologique</div>
        <div class="legend-item"><div class="dot" style="background: var(--accent-red); color: var(--accent-red);"></div> Caserne de secours</div>
        <div class="legend-item"><div class="dot" style="background: var(--accent-emerald); color: var(--accent-emerald);"></div> Centre hospitalier</div>
        <div class="legend-item"><div class="dot" style="background: var(--accent-cyan); color: var(--accent-cyan);"></div> Hub télécommunication</div>
        <div class="legend-item"><div class="dot" style="background: #818cf8; color: #818cf8;"></div> Efrei Paris (Campus Villejuif)</div>
        <div class="legend-item"><div class="dot" style="background: #a855f7; color: #a855f7;"></div> Établissement scolaire</div>
        <div class="legend-item"><div class="dot" style="background: var(--accent-amber); color: var(--accent-amber);"></div> Quartier résidentiel</div>
        <div class="legend-item"><div class="line-swatch" style="background: #94a3b8; height: 2px;"></div> Arcs du graphe</div>
        <div class="legend-item"><div class="line-swatch" style="background: var(--accent-red); height: 2px;"></div> Axe fermé (crise)</div>
        <div class="legend-item"><div class="line-swatch" style="background: var(--accent-emerald); height: 3px;"></div> Itinéraire retenu</div>
        <div class="legend-item"><div class="line-swatch" style="background: var(--accent-cyan); height: 2px;"></div> Réseau fibre MST</div>
        <div class="legend-item"><div class="line-swatch" style="background: var(--accent-amber); height: 3px;"></div> Tronçon de secours</div>
    </div>

    <div id="leaflet-map"></div>
</div>

<!-- Modal Matrice de Résilience Multiscénario -->
<div id="matrix-modal" onclick="fermerMatriceSiExterieur(event)">
    <div class="modal-card">
        <div class="modal-header">
            <div style="font-weight: 700; font-size: 1rem;">Matrice Comparative de Résilience (Module 5)</div>
            <button class="modal-close" onclick="fermerMatrice()">&times;</button>
        </div>
        <table class="matrix-table">
            <thead>
                <tr>
                    <th>Scénario</th>
                    <th>Demandes Perdues</th>
                    <th>Retard Moyen</th>
                    <th>Retard Max</th>
                    <th>Sensibles %</th>
                    <th>Comp. Fibre</th>
                    <th>Réparation</th>
                </tr>
            </thead>
            <tbody id="matrix-tbody"></tbody>
        </table>
    </div>
</div>

<script>
    let DATA = null;
    let map = null;
    let baseLayer = null;

    let markersLayer = L.layerGroup();
    let routesLayer = L.layerGroup();
    let fibreLayer = L.layerGroup();
    let secoursLayer = L.layerGroup();
    let panneLayer = L.layerGroup();

    let afficherFibre = true;
    let afficherRoutes = false;
    let modeVoirieReelle = true;
    let modePointe = false;

    const FOND_TILES = {
        esri_dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        google_roadmap: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        google_hybrid: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        osm_standard: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
    };

    function initMap() {
        map = L.map('leaflet-map', {
            zoomControl: false,
            attributionControl: false
        }).setView([48.8566, 2.3522], 12);

        baseLayer = L.tileLayer(FOND_TILES.esri_dark, { maxZoom: 19 }).addTo(map);
        L.control.zoom({ position: 'bottomleft' }).addTo(map);

        // Hiérarchie stricte des plans SVG pour empêcher toute superposition du tracé sur les sommets
        map.createPane('routesPane');
        map.getPane('routesPane').style.zIndex = 400;

        map.createPane('fibrePane');
        map.getPane('fibrePane').style.zIndex = 420;

        map.createPane('secoursPane');
        map.getPane('secoursPane').style.zIndex = 450;

        map.createPane('markersPane');
        map.getPane('markersPane').style.zIndex = 650;

        map.createPane('activeNodePane');
        map.getPane('activeNodePane').style.zIndex = 680;

        routesLayer.addTo(map);
        fibreLayer.addTo(map);
        panneLayer.addTo(map);
        secoursLayer.addTo(map);
        markersLayer.addTo(map);
    }

    function changerFondCarto() {
        let style = document.getElementById("select-basemap").value;
        map.removeLayer(baseLayer);
        baseLayer = L.tileLayer(FOND_TILES[style], { maxZoom: 19 }).addTo(map);
        baseLayer.bringToBack();
    }

    async function chargerDonnees(dataset, scenario) {
        let resp = await fetch(`/api/data?dataset=${encodeURIComponent(dataset)}&scenario=${encodeURIComponent(scenario)}&poids=${modePointe ? "temps_pointe" : "temps_normal"}`);
        DATA = await resp.json();

        // 1. Scénarios
        let scSelect = document.getElementById("select-scenario");
        scSelect.innerHTML = "";
        DATA.scenarios_disponibles.forEach(sc => {
            let opt = document.createElement("option");
            opt.value = sc;
            opt.textContent = sc.replace(/_/g, " ").toUpperCase();
            if (sc === DATA.scenario) opt.selected = true;
            scSelect.appendChild(opt);
        });

        // 2. Sélecteurs Origine / Destination
        let depSelect = document.getElementById("select-depart");
        let arrSelect = document.getElementById("select-arrivee");
        let cableSelect = document.getElementById("select-cable-cut");
        depSelect.innerHTML = "";
        arrSelect.innerHTML = "";
        cableSelect.innerHTML = "";

        Object.values(DATA.sites).forEach(s => {
            let isEfrei = s.id === "SITE_111";
            let opt1 = document.createElement("option");
            opt1.value = s.id;
            opt1.textContent = isEfrei ? `${s.id} — ${s.nom} ⭐ (Efrei Paris)` : `${s.id} — ${s.nom}`;
            if (s.type === "caserne") depSelect.appendChild(opt1);

            let opt2 = document.createElement("option");
            opt2.value = s.id;
            opt2.textContent = isEfrei ? `${s.id} — ${s.nom} ⭐ (Efrei Paris)` : `${s.id} — ${s.nom}`;
            arrSelect.appendChild(opt2);
        });

        // 3. Tronçons fibre MST pour coupure
        DATA.mst_fibre.forEach(paire => {
            let opt = document.createElement("option");
            opt.value = `${paire[0]}__${paire[1]}`;
            opt.textContent = `${paire[0]} ↔ ${paire[1]}`;
            cableSelect.appendChild(opt);
        });

        // 4. Métriques
        document.getElementById("kpi-temps").textContent = "—";
        document.getElementById("kpi-retard").textContent = "+0.0 min";
        document.getElementById("kpi-retard").className = "metric-value status-ok";
        document.getElementById("itinerary-log").style.display = "none";
        secoursLayer.clearLayers();
        document.getElementById("kpi-sensibles").textContent = DATA.diagnostic.sensibles_couverts;
        document.getElementById("kpi-fibre").textContent = `${DATA.cout_mst} k€`;

        dessinerCarte();
        recentrerVueParis();
    }

    function changerEnvironnement() {
        let ds = document.getElementById("select-dataset").value;
        chargerDonnees(ds, "scenario_normal");
    }

    function changerScenario() {
        let ds = document.getElementById("select-dataset").value;
        let sc = document.getElementById("select-scenario").value;
        chargerDonnees(ds, sc);
    }

    function recentrerVueParis() {
        if (!DATA) return;
        let coords = Object.values(DATA.sites).map(s => [s.lat, s.lng]);
        if (coords.length > 0) {
            let bounds = L.latLngBounds(coords);
            map.fitBounds(bounds, { padding: [40, 40] });
        }
    }

    function dessinerCarte() {
        routesLayer.clearLayers();
        fibreLayer.clearLayers();
        markersLayer.clearLayers();
        secoursLayer.clearLayers();
        panneLayer.clearLayers();

        // 1. Routes (ou uniquement les axes fermés si arcs désactivés)
        if (afficherRoutes) {
            DATA.routes.forEach(r => {
                let s1 = DATA.sites[r.u];
                let s2 = DATA.sites[r.v];
                if (!s1 || !s2) return;

                let latlngs = [[s1.lat, s1.lng], [s2.lat, s2.lng]];
                if (!r.ouvert) {
                    L.polyline(latlngs, {
                        pane: 'routesPane',
                        color: '#f43f5e',
                        weight: 3.5,
                        dashArray: '5, 5',
                        opacity: 0.95
                    }).bindTooltip(`Axe bloqué : ${r.u} ➔ ${r.v}`).addTo(routesLayer);
                } else {
                    L.polyline(latlngs, {
                        pane: 'routesPane',
                        color: '#94a3b8',
                        weight: 2,
                        opacity: 0.75
                    }).addTo(routesLayer);
                }
            });
        } else {
            DATA.routes.forEach(r => {
                if (!r.ouvert) {
                    let s1 = DATA.sites[r.u];
                    let s2 = DATA.sites[r.v];
                    if (!s1 || !s2) return;
                    L.polyline([[s1.lat, s1.lng], [s2.lat, s2.lng]], {
                        pane: 'routesPane',
                        color: '#f43f5e',
                        weight: 3.5,
                        dashArray: '5, 5',
                        opacity: 0.95
                    }).bindTooltip(`Axe fermé (scénario) : ${r.u} ➔ ${r.v}`).addTo(routesLayer);
                }
            });
        }

        // 2. Fibre optique (Arbre couvrant minimal)
        if (afficherFibre) {
            DATA.mst_fibre.forEach(paire => {
                let s1 = DATA.sites[paire[0]];
                let s2 = DATA.sites[paire[1]];
                if (s1 && s2) {
                    L.polyline([[s1.lat, s1.lng], [s2.lat, s2.lng]], {
                        pane: 'fibrePane',
                        color: '#0090ff',
                        weight: 2,
                        opacity: 0.75,
                        dashArray: '3, 4'
                    }).addTo(fibreLayer);
                }
            });
        }

        // 3. Sommets (Sites réels de Paris & Campus Efrei)
        const COULEURS = {
            caserne: "#e5484d",
            hopital: "#30a46c",
            telecom: "#0090ff",
            ecole: "#a855f7",
            quartier: "#f5a623"
        };

        Object.values(DATA.sites).forEach(s => {
            let isEfrei = s.id === "SITE_111";
            let col = isEfrei ? "#6366f1" : (COULEURS[s.type] || "#8e95a0");
            let radius = isEfrei ? 8 : ((s.type === "caserne" || s.type === "hopital") ? 6.5 : 4.5);

            let marker = L.circleMarker([s.lat, s.lng], {
                pane: 'markersPane',
                radius: radius,
                fillColor: col,
                color: isEfrei ? '#c7d2fe' : '#ffffff',
                weight: isEfrei ? 2.5 : 2,
                opacity: 1,
                fillOpacity: 0.95
            });

            let typeLabel = isEfrei ? "Campus Académique Efrei Paris (Villejuif)" : s.type;
            marker.bindTooltip(`<strong>${s.id}</strong> — ${s.nom} <div style="font-size:0.7rem;color:#9aa2b1;margin-top:2px;">${typeLabel}</div>`, {
                direction: 'top',
                offset: [0, -6]
            });
            marker.on('click', () => {
                document.getElementById("select-arrivee").value = s.id;
            });
            marker.addTo(markersLayer);
        });
    }

    let animSecoursId = null;

    function nettoyerBouclesRedondantes(coords, ptDepart, ptArrivee) {
        if (!coords || coords.length < 10) return coords;
        let res = [...coords];
        let ameliore = true;
        let tour = 0;
        while (ameliore && tour < 10) {
            ameliore = false;
            tour++;
            for (let i = 0; i < res.length - 4; i++) {
                for (let j = i + 4; j < Math.min(i + 80, res.length); j++) {
                    let dLat = Math.abs(res[i][0] - res[j][0]);
                    let dLng = Math.abs(res[i][1] - res[j][1]);
                    if (dLat < 0.00035 && dLng < 0.00035) {
                        let hasDest = false;
                        if (ptArrivee) {
                            for (let k = i; k <= j; k++) {
                                if (Math.abs(res[k][0] - ptArrivee[0]) < 0.0003 && Math.abs(res[k][1] - ptArrivee[1]) < 0.0003) {
                                    hasDest = true;
                                    break;
                                }
                            }
                        }
                        if (!hasDest) {
                            res.splice(i + 1, j - i);
                            ameliore = true;
                            break;
                        }
                    }
                }
                if (ameliore) break;
            }
        }
        return res;
    }

    function animerTraceProgressif(pathCoords) {
        if (animSecoursId) {
            cancelAnimationFrame(animSecoursId);
            animSecoursId = null;
        }

        secoursLayer.clearLayers();
        if (!pathCoords || pathCoords.length === 0) return;

        if (pathCoords.length === 1) {
            L.circleMarker(pathCoords[0], {
                pane: 'activeNodePane',
                radius: 6,
                color: '#30a46c',
                fillColor: '#30a46c',
                fillOpacity: 0.95
            }).addTo(secoursLayer);
            return;
        }

        let haloGlow = L.polyline([], {
            pane: 'secoursPane',
            color: 'rgba(48, 164, 108, 0.28)',
            weight: 9,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(secoursLayer);

        let lignePrincipale = L.polyline([], {
            pane: 'secoursPane',
            color: '#30a46c',
            weight: 4.5,
            opacity: 0.98,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(secoursLayer);

        let leadMarker = L.circleMarker(pathCoords[0], {
            pane: 'activeNodePane',
            radius: 6,
            color: '#ffffff',
            fillColor: '#30a46c',
            fillOpacity: 1,
            weight: 2
        }).addTo(secoursLayer);

        const DUREE_ANIM_MS = 1100;
        let startTime = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            let elapsed = timestamp - startTime;
            let progress = Math.min(elapsed / DUREE_ANIM_MS, 1.0);

            let eased = 1 - Math.pow(1 - progress, 3);
            let targetIdx = Math.max(1, Math.floor(eased * (pathCoords.length - 1)));
            let currentSlice = pathCoords.slice(0, targetIdx + 1);

            haloGlow.setLatLngs(currentSlice);
            lignePrincipale.setLatLngs(currentSlice);

            if (currentSlice.length > 0) {
                leadMarker.setLatLng(currentSlice[currentSlice.length - 1]);
            }

            if (progress < 1.0) {
                animSecoursId = requestAnimationFrame(step);
            } else {
                animSecoursId = null;
                setTimeout(() => {
                    if (secoursLayer.hasLayer(leadMarker)) {
                        leadMarker.remove();
                    }
                }, 350);
            }
        }

        animSecoursId = requestAnimationFrame(step);
    }

    async function calculerItineraireDijkstra() {
        let dep = document.getElementById("select-depart").value;
        let arr = document.getElementById("select-arrivee").value;
        let ds = document.getElementById("select-dataset").value;
        let sc = document.getElementById("select-scenario").value;

        if (animSecoursId) {
            cancelAnimationFrame(animSecoursId);
            animSecoursId = null;
        }
        secoursLayer.clearLayers();

        let resp = await fetch(`/api/dijkstra?dataset=${encodeURIComponent(ds)}&scenario=${encodeURIComponent(sc)}&source=${dep}&cible=${arr}&poids=${modePointe ? "temps_pointe" : "temps_normal"}`);
        let res = await resp.json();

        let logDiv = document.getElementById("itinerary-log");

        if (res.accessible) {
            document.getElementById("kpi-temps").textContent = `${res.duree} min`;
            document.getElementById("kpi-retard").textContent = `+${res.retard} min`;
            document.getElementById("kpi-retard").className = res.retard > 0 ? "metric-value status-alert" : "metric-value status-ok";

            let pathCoords = res.chemin.map(id => [DATA.sites[id].lat, DATA.sites[id].lng]);

            if (modeVoirieReelle && res.chemin.length >= 2) {
                try {
                    let coordsParam = res.chemin.map(id => `${DATA.sites[id].lng},${DATA.sites[id].lat}`).join(";");
                    let osrmUrl = `https://router.project-osrm.org/route/v1/driving/${coordsParam}?overview=full&geometries=geojson&continue_straight=true`;
                    let rOsrm = await fetch(osrmUrl);
                    let dOsrm = await rOsrm.json();
                    if (dOsrm.code === "Ok" && dOsrm.routes && dOsrm.routes.length > 0) {
                        pathCoords = dOsrm.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
                    }
                } catch (err) {
                    console.warn("Fallback sur le trace direct topologique", err);
                }
            }

            let ptDep = [DATA.sites[dep].lat, DATA.sites[dep].lng];
            let ptArr = [DATA.sites[arr].lat, DATA.sites[arr].lng];
            pathCoords = nettoyerBouclesRedondantes(pathCoords, ptDep, ptArr);

            animerTraceProgressif(pathCoords);

            // Cercles concentriques d'accentuation sur le départ et l'arrivée dans le plan actif
            L.circleMarker(ptDep, {
                pane: 'activeNodePane',
                radius: 12,
                color: '#e5484d',
                weight: 2.5,
                fill: false,
                opacity: 0.95
            }).addTo(secoursLayer);

            let arrColor = arr === "SITE_111" ? '#818cf8' : '#30a46c';
            L.circleMarker(ptArr, {
                pane: 'activeNodePane',
                radius: arr === "SITE_111" ? 14 : 12,
                color: arrColor,
                weight: 3,
                fill: false,
                opacity: 0.95
            }).addTo(secoursLayer);

            if (pathCoords && pathCoords.length > 1) {
                map.fitBounds(L.latLngBounds(pathCoords), { padding: [60, 60], maxZoom: 15 });
            }

            logDiv.style.display = "block";
            let stepsHtml = res.chemin.map((id, idx) => {
                let s = DATA.sites[id];
                let isFirst = idx === 0;
                let isLast = idx === res.chemin.length - 1;
                let isEfrei = id === "SITE_111";
                let dotColor = isFirst ? "var(--accent-red)" : (isLast ? (isEfrei ? "#818cf8" : "var(--accent-green)") : "var(--accent-cyan)");
                let role = isFirst ? "Origine (Départ)" : (isLast ? (isEfrei ? "Destination • Campus Efrei Paris" : "Destination (Arrivée)") : "Étape de transit");
                let roleType = s ? `${role} • ${s.type}` : role;
                let nom = s ? s.nom : id;
                return `
                <div class="itinerary-step" onclick="centrerEtape('${id}')" title="Cliquer pour centrer la carte sur ${nom}">
                    <div class="step-indicator">
                        <span class="step-dot" style="background:${dotColor};"></span>
                        ${!isLast ? '<span class="step-line"></span>' : ''}
                    </div>
                    <div class="step-content">
                        <div class="step-top">
                            <span class="step-name" title="${nom}">${nom}</span>
                            <span class="step-id">${id}</span>
                        </div>
                        <div class="step-role">${roleType}</div>
                    </div>
                </div>`;
            }).join("");

            logDiv.innerHTML = `
                <div class="itinerary-header">
                    <span class="itinerary-title">Feuille de Route (${res.nb_arcs} segments)</span>
                    <span class="itinerary-badge">${res.duree} min</span>
                </div>
                <div class="itinerary-timeline">
                    ${stepsHtml}
                </div>
            `;
        } else {
            document.getElementById("kpi-temps").textContent = "Inaccessible";
            document.getElementById("kpi-retard").textContent = "∞";
            document.getElementById("kpi-retard").className = "metric-value status-alert";

            logDiv.style.display = "block";
            let sDep = DATA.sites[dep] ? DATA.sites[dep].nom : dep;
            let sArr = DATA.sites[arr] ? DATA.sites[arr].nom : arr;
            logDiv.innerHTML = `
                <div class="itinerary-header">
                    <span class="itinerary-title" style="color:var(--accent-red);">Itinéraire Rompu</span>
                    <span class="itinerary-badge" style="color:var(--accent-red);background:rgba(229,72,77,0.12);border:1px solid rgba(229,72,77,0.3);">Inaccessible</span>
                </div>
                <div style="font-size:0.75rem;color:var(--text-secondary);line-height:1.4;">
                    Aucun chemin praticable n'existe entre <strong style="color:var(--text-primary);">${sDep}</strong> et <strong style="color:var(--text-primary);">${sArr}</strong> sous ce scénario.
                </div>
            `;
        }
    }

    function lancerDemoEfrei() {
        let depSelect = document.getElementById("select-depart");
        let arrSelect = document.getElementById("select-arrivee");
        depSelect.value = "SITE_046"; // Caserne Masséna (13e)
        arrSelect.value = "SITE_111"; // Campus Efrei Paris (Villejuif)
        calculerItineraireDijkstra();
    }

    function centrerSurEfrei() {
        if (!DATA || !DATA.sites["SITE_111"]) return;
        let efrei = DATA.sites["SITE_111"];
        map.flyTo([efrei.lat, efrei.lng], 16, { duration: 1.2 });
    }

    function centrerEtape(id) {
        if (!DATA || !DATA.sites[id]) return;
        let s = DATA.sites[id];
        map.flyTo([s.lat, s.lng], 16, { duration: 0.8 });
    }

    function toggleVoirie() {
        modeVoirieReelle = !modeVoirieReelle;
        document.getElementById("btn-voirie").classList.toggle("active", modeVoirieReelle);
        calculerItineraireDijkstra();
    }

    function toggleRoutesGraphe() {
        afficherRoutes = !afficherRoutes;
        document.getElementById("btn-routes").classList.toggle("active", afficherRoutes);
        dessinerCarte();
    }

    async function simulerCoupureCable() {
        let val = document.getElementById("select-cable-cut").value;
        if (!val) return;
        let [u, v] = val.split("__");
        let ds = document.getElementById("select-dataset").value;
        let sc = document.getElementById("select-scenario").value;

        panneLayer.clearLayers();

        let resp = await fetch(`/api/cut_fiber?dataset=${encodeURIComponent(ds)}&scenario=${encodeURIComponent(sc)}&u=${u}&v=${v}`);
        let res = await resp.json();

        let s1 = DATA.sites[u];
        let s2 = DATA.sites[v];
        if (s1 && s2) {
            L.polyline([[s1.lat, s1.lng], [s2.lat, s2.lng]], {
                pane: 'secoursPane',
                color: '#e5484d',
                weight: 4,
                dashArray: '4, 4'
            }).addTo(panneLayer);
        }

        if (res.succes_reparation && res.arete_remplacement) {
            let [ru, rv] = res.arete_remplacement;
            let rs1 = DATA.sites[ru];
            let rs2 = DATA.sites[rv];
            if (rs1 && rs2) {
                L.polyline([[rs1.lat, rs1.lng], [rs2.lat, rs2.lng]], {
                    pane: 'secoursPane',
                    color: '#f5a623',
                    weight: 4
                }).bindTooltip(`Raccordement de secours : ${ru} ↔ ${rv} (+${res.cout_remplacement} k€)`).openTooltip().addTo(panneLayer);
            }
            let msg = `Coupure simulee sur ${u} ↔ ${v}.\nRaccordement optimal identifie : ${ru} ↔ ${rv} (Cout : ${res.cout_remplacement} k€, Surcout : +${res.surcout} k€).`;
            if (window.__modeAutoTest) {
                mettreAJourBanniere(msg.split(String.fromCharCode(10)).join(" — "), "#f5a623");
            } else {
                alert(msg);
            }
        } else {
            let msg = `Coupure simulee sur ${u} ↔ ${v}.\nAucun raccordement de secours disponible : le reseau est disloque en composantes isolees.`;
            if (window.__modeAutoTest) {
                mettreAJourBanniere(msg.split(String.fromCharCode(10)).join(" — "), "#e5484d");
            } else {
                alert(msg);
            }
        }
    }

    function toggleFibre() {
        afficherFibre = !afficherFibre;
        document.getElementById("btn-fibre").classList.toggle("active", afficherFibre);
        dessinerCarte();
    }

    function togglePointe() {
        modePointe = !modePointe;
        document.getElementById("btn-pointe").classList.toggle("active", modePointe);
        calculerItineraireDijkstra();
    }

    function ouvrirMatriceResilience() {
        let tbody = document.getElementById("matrix-tbody");
        tbody.innerHTML = "";
        Object.entries(DATA.matrice_resilience).forEach(([sc_id, m]) => {
            let tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${sc_id.replace(/_/g, " ")}</td>
                <td>${m.demandes_perdues} (${m.pourcentage_perdues}%)</td>
                <td>+${m.retard_moyen} min</td>
                <td>+${m.retard_max} min</td>
                <td>${m.sensibles_pct}%</td>
                <td>${m.composantes_fibre}</td>
                <td>${m.cout_reparation} k€</td>
            `;
            tbody.appendChild(tr);
        });
        document.getElementById("matrix-modal").style.display = "flex";
    }

    function fermerMatrice() {
        document.getElementById("matrix-modal").style.display = "none";
    }

    function fermerMatriceSiExterieur(e) {
        if (e.target.id === "matrix-modal") fermerMatrice();
    }

    window.onload = () => {
        initMap();
        chargerDonnees("data/realiste", "scenario_normal");
    };
</script>
</body>
</html>
"""


class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    """Serveur HTTP API et interface cartographique sans dépendance externe."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif path == "/api/data":
            dataset = params.get("dataset", ["data/realiste"])[0]
            scenario = params.get("scenario", ["scenario_normal"])[0]
            poids = params.get("poids", ["temps_normal"])[0]
            try:
                data = preparer_donnees_json(dataset, scenario, poids=poids)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/dijkstra":
            dataset = params.get("dataset", ["data/realiste"])[0]
            scenario = params.get("scenario", ["scenario_normal"])[0]
            source = params.get("source", ["SITE_001"])[0]
            cible = params.get("cible", ["SITE_027"])[0]
            poids = params.get("poids", ["temps_normal"])[0]

            reseau_base = obtenir_reseau_base(dataset)
            reseau_pert = appliquer_scenario(reseau_base, scenario)

            dist_av, _ = dijkstra(reseau_base.routier, source, poids=poids)
            t_av = dist_av.get(cible, math.inf)

            dist_ap, pred_ap = dijkstra(reseau_pert.routier, source, poids=poids)
            t_ap = dist_ap.get(cible, math.inf)

            if t_ap != math.inf:
                chemin = reconstruire_chemin(pred_ap, source, cible)
                retard = max(0.0, t_ap - t_av) if t_av != math.inf else 0.0
                reponse = {
                    "accessible": True,
                    "chemin": chemin,
                    "duree": round(t_ap, 2),
                    "retard": round(retard, 2),
                    "nb_arcs": len(chemin) - 1,
                }
            else:
                reponse = {
                    "accessible": False,
                    "chemin": [],
                    "duree": None,
                    "retard": None,
                    "nb_arcs": 0,
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(reponse).encode("utf-8"))

        elif path == "/api/cut_fiber":
            dataset = params.get("dataset", ["data/realiste"])[0]
            scenario = params.get("scenario", ["scenario_normal"])[0]
            u = params.get("u", [""])[0]
            v = params.get("v", [""])[0]

            reseau_base = obtenir_reseau_base(dataset)
            reseau_pert = appliquer_scenario(reseau_base, scenario)
            mst_res = kruskal(reseau_pert.fibre)

            try:
                res_panne = simuler_panne_troncon(reseau_pert.fibre, mst_res["aretes"], (u, v))
                remp = list(res_panne["arete_remplacement"]) if res_panne["arete_remplacement"] else None
                reponse = {
                    "succes_reparation": res_panne["succes_reparation"],
                    "arete_remplacement": remp,
                    "cout_remplacement": res_panne["cout_remplacement"],
                    "surcout": res_panne["surcout"],
                }
            except Exception as e:
                reponse = {
                    "succes_reparation": False,
                    "arete_remplacement": None,
                    "cout_remplacement": None,
                    "surcout": None,
                    "error": str(e),
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(reponse).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def lancer_serveur(port: int = PORT_DEFAUT):
    """Lance le serveur web local sur le port spécifié."""
    with ThreadedTCPServer(("", port), DashboardRequestHandler) as httpd:
        print("=" * 80)
        print("SERVEUR NOVAPOLIS RESILIENCE (PARIS CARTOGRAPHIE REELLE) OPERATIONNEL")
        print(f"Ouvrez votre navigateur : http://localhost:{port}")
        print("Appuyez sur Ctrl+C pour interrompre le serveur.")
        print("=" * 80)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nArret du serveur web.")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT_DEFAUT
    lancer_serveur(port)
