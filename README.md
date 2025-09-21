# Solar Panel Monitoring System

A real-time monitoring system for photovoltaic panels with MPP (Maximum Power Point) tracking.

## Project Structure

```
.
├── backend/           # FastAPI backend
├── frontend/          # React + Vite frontend
├── docker-compose.yml # Docker Compose configuration
├── .env.example       # Example environment variables (root convenience)
└── README.md         # This file
```

## Prérequis

- Docker Desktop (inclut docker compose)

## Démarrage rapide (Docker uniquement)

1. (Optionnel) Copier les variables d'exemple si vous souhaitez surcharger par défaut:
   - `backend/.env.example` et `frontend/.env.example` listent les variables disponibles.

2. Lancer l'application:
   ```bash
   docker compose up --build
   ```

3. Accès:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs

Le projet est exécutable exclusivement via Docker. Aucun package local n'est requis.

## Variables d'environnement

- Backend (`backend/.env.example`): `API_PORT`, `DATABASE_URL` (SQLite par défaut en dev, PostgreSQL possible), `API_TOKEN`, `WS_ENABLED`, `BLYNK_TOKEN?`, `VPIN_V?`, `VPIN_I?`, `VPIN_T?`.
- Frontend (`frontend/.env.example`): `VITE_API_BASE_URL`, `VITE_WS_URL`, `VITE_API_TOKEN`.

## API principale

- `POST /api/samples` (protégé Bearer): body JSON objet ou tableau `{t?: ISODate, V: number, I: number, P?: number, T?: number, source?: string}`. Si `P` manquant, calcul automatique `P=V*I`.
- `GET /api/samples?from=&to=&limit=`: renvoie la série triée par temps.
- `GET /api/mpp?from=&to=`: renvoie `{Vmp, Imp, Pmp, index, t}`.
- `POST /api/import/text` (protégé Bearer): accepte `text/plain` (brut) ou JSON `{text: "..."}` avec lignes `V:..V I:..A P:..W`.
- `GET /api/health`: statut service.
- WebSocket `/ws/live`: diffuse les nouveaux points.

### Exemples de requêtes

Token par défaut (docker compose): `devtoken`.

Insérer des échantillons (JSON):
```bash
docker compose exec backend sh -lc "curl -s -X POST http://localhost:8000/api/samples \
  -H 'Authorization: Bearer devtoken' -H 'Content-Type: application/json' \
  -d '[{"V":0,"I":5},{"V":5,"I":4},{"V":10,"I":3},{"V":15,"I":1}]' | jq ."
```

Importer du texte brut:
```bash
docker compose exec backend sh -lc "printf 'V:20.2V I:0.10A P:2.1W\nV:1.7V I:17.24A P:28.8W\n' \
  | curl -s -X POST http://localhost:8000/api/import/text \
    -H 'Authorization: Bearer devtoken' -H 'Content-Type: text/plain' \
    --data-binary @- | jq ."
```

Lire MPP:
```bash
curl -s http://localhost:8000/api/mpp | jq .
```

## UI (Frontend)

- Dashboard avec KPI (V, I, P, T), statut WebSocket.
- Graphes I-V (scatter + lissage optionnel) et P-V avec MPP mis en évidence.
- Détection et affichage Voc (I≈0) et Isc (V≈0).
- Import texte/CSV, export CSV et PNG (via barre d'outils Plotly).

Plotting: Plotly.js (via `react-plotly.js`) est choisi pour sa facilité d'export PNG intégré et ses fonctionnalités d'annotation (MPP).
État: Zustand est utilisé pour sa simplicité et un boilerplate minimal par rapport à Redux.

## Script passerelle série (optionnel)

Un script Python est fourni: `backend/app/scripts/serial_bridge.py`.

Usage local:
```bash
python backend/app/scripts/serial_bridge.py --port COM3 --baud 115200 --api http://localhost:8000 --token devtoken
```
Il accepte des lignes au format texte `V:..V I:..A P:..W` ou JSON `{V,I,P?}` et pousse vers l'API.

## License

This project is licensed under the MIT License.
