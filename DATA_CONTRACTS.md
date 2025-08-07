# Contrats de Données - Service Intervention

## Vue d'ensemble

Ce document définit les contrats de données pour le **service intervention**. Il garantit une intégration cohérente entre le backend et le frontend en spécifiant les structures exactes des données échangées.

**Version**: 1.0  
**Service**: intervention_service  
**Port**: 8006  
**Base URL**: `/api/`  

---

## 📋 Index des Contrats

### Gestion des Interventions (`/interventions/`)
- [Intervention](#intervention) - Interventions principales
- [InterventionTask](#interventiontask) - Tâches d'intervention
- [InterventionMaterial](#interventionmaterial) - Matériaux utilisés
- [InterventionReport](#interventionreport) - Rapports d'intervention
- [InterventionPhoto](#interventionphoto) - Photos d'intervention

### Entités de Support
- [Client](#client) - Clients demandeurs
- [Technicien](#technicien) - Techniciens intervenant

### Utilitaires (`/api/`)
- [Statistics](#statistics) - Statistiques d'intervention
- [HealthCheck](#healthcheck) - État du service

---

## 🏗️ Contrats Gestion des Interventions

### Intervention
**Endpoint**: `GET/POST /api/interventions/`

```json
{
  "id": "integer (readonly)",
  "titre": "string (max: 200)",
  "description": "string",
  "client": "integer (foreign key)",
  "client_nom": "string (readonly)",
  "technicien": "integer (foreign key, optional)",
  "technicien_nom": "string (readonly)",
  "statut": "PLANIFIEE | EN_COURS | TERMINEE | ANNULEE",
  "statut_display": "string (readonly)",
  "priorite": "BASSE | NORMALE | HAUTE | URGENTE",
  "priorite_display": "string (readonly)",
  "date_planifiee": "datetime",
  "date_debut": "datetime (optional)",
  "date_fin": "datetime (optional)",
  "duree_estimee_minutes": "integer (min: 15, default: 60)",
  "duree_reelle_minutes": "integer (readonly, calculated)",
  "cout_materiel": "decimal (10,2, default: 0.00)",
  "cout_main_oeuvre": "decimal (10,2, default: 0.00)",
  "cout_total": "decimal (readonly, calculated)",
  "tenant_id": "string (max: 36)",
  "date_creation": "datetime (readonly)",
  "date_modification": "datetime (readonly)",
  "tasks": "array (nested, readonly)",
  "materials": "array (nested, readonly)",
  "reports": "array (nested, readonly)",
  "photos": "array (nested, readonly)"
}
```

**Validation**:
- `titre`: Requis, 1-200 caractères
- `client`: Requis, doit exister
- `date_planifiee`: Requis, doit être future pour créations
- `statut`: Par défaut `PLANIFIEE`
- `priorite`: Par défaut `NORMALE`

**Champs calculés**:
- `duree_reelle_minutes = (date_fin - date_debut) en minutes`
- `cout_total = cout_materiel + cout_main_oeuvre`

**Actions disponibles**:
- `POST /api/interventions/{id}/demarrer/` - Démarre l'intervention
- `POST /api/interventions/{id}/terminer/` - Termine l'intervention  
- `POST /api/interventions/{id}/annuler/` - Annule l'intervention
- `POST /api/interventions/{id}/assigner/` - Assigne un technicien

---

### InterventionTask
**Endpoint**: `GET/POST /api/interventions/{intervention_id}/tasks/`

```json
{
  "id": "integer (readonly)",
  "intervention": "integer (foreign key, readonly)",
  "description": "string (max: 255)",
  "est_complete": "boolean (default: false)",
  "date_creation": "datetime (readonly)",
  "date_modification": "datetime (readonly)"
}
```

**Validation**:
- `description`: Requis, 1-255 caractères
- `intervention`: Auto-assigné depuis l'URL

---

### InterventionMaterial
**Endpoint**: `GET/POST /api/interventions/{intervention_id}/materials/`

```json
{
  "id": "integer (readonly)",
  "intervention": "integer (foreign key, readonly)",
  "nom": "string (max: 100)",
  "quantite": "integer (min: 1, default: 1)",
  "prix_unitaire": "decimal (10,2, min: 0.00)",
  "prix_total": "decimal (readonly, calculated)",
  "date_creation": "datetime (readonly)",
  "date_modification": "datetime (readonly)"
}
```

**Champs calculés**:
- `prix_total = quantite * prix_unitaire`

**Post-traitement**:
- Met à jour automatiquement `intervention.cout_materiel`

---

### InterventionReport
**Endpoint**: `GET/POST /api/interventions/{intervention_id}/reports/`

```json
{
  "id": "integer (readonly)",
  "intervention": "integer (foreign key, readonly)",
  "contenu": "string",
  "date_creation": "datetime (readonly)",
  "date_modification": "datetime (readonly)"
}
```

**Validation**:
- `contenu`: Requis, texte libre pour rapport détaillé

---

### InterventionPhoto
**Endpoint**: `GET/POST /api/interventions/{intervention_id}/photos/`

```json
{
  "id": "integer (readonly)",
  "intervention": "integer (foreign key, readonly)",
  "image": "file (upload)",
  "image_url": "string (readonly)",
  "description": "string (max: 255, optional)",
  "date_creation": "datetime (readonly)"
}
```

**Upload**:
- Format accepté: JPG, PNG, WebP
- Taille max: 5MB
- Stockage: `interventions/photos/`

---

## 👥 Contrats Entités de Support

### Client
**Endpoint**: `GET/POST /api/clients/` (Admin uniquement)

```json
{
  "id": "integer (readonly)",
  "nom": "string (max: 100)",
  "adresse": "string",
  "email": "email (optional)",
  "telephone": "string (max: 20)",
  "tenant_id": "string (max: 36)",
  "crm_id": "string (max: 36, optional)",
  "date_creation": "datetime (readonly)",
  "date_modification": "datetime (readonly)",
  "interventions_count": "integer (readonly)"
}
```

**Intégration externe**:
- `crm_id`: Référence vers le service CRM
- `tenant_id`: Isolation multi-tenant

---

### Technicien
**Endpoint**: `GET/POST /api/techniciens/` (Admin uniquement)

```json
{
  "id": "integer (readonly)",
  "nom": "string (max: 100)",
  "prenom": "string (max: 100)",
  "email": "email (unique)",
  "telephone": "string (max: 20, optional)",
  "specialite": "string (max: 100, optional)",
  "disponible": "boolean (default: true)",
  "date_creation": "datetime (readonly)",
  "date_modification": "datetime (readonly)",
  "interventions_actives": "integer (readonly)",
  "nom_complet": "string (readonly)"
}
```

**Champs calculés**:
- `nom_complet = prenom + ' ' + nom`
- `interventions_actives`: Nombre d'interventions EN_COURS

---

## 📊 Contrats Utilitaires

### Statistics
**Endpoint**: `GET /api/stats/`

```json
[
  {
    "statut": "PLANIFIEE",
    "total": 15
  },
  {
    "statut": "EN_COURS", 
    "total": 8
  },
  {
    "statut": "TERMINEE",
    "total": 42
  },
  {
    "statut": "ANNULEE",
    "total": 3
  }
]
```

**Cache**: 30 secondes

---

### HealthCheck
**Endpoint**: `GET /api/health/`

```json
{
  "status": "ok",
  "timestamp": "2025-08-07T10:30:00Z",
  "version": "1.0.0",
  "database": "connected"
}
```

---

## 🔗 Relations et Dépendances

### Schéma relationnel
```
Client ←--→ Intervention ←--→ Technicien
               ↓
         ┌─────┼─────┬─────┬─────┐
         ↓     ↓     ↓     ↓     ↓
  Task  Mat.  Rep.  Photo  ...
```

### Cascade de suppression
- `Client` supprimé → Interventions protégées (erreur)
- `Intervention` supprimée → Tasks, Materials, Reports, Photos supprimés
- `Technicien` supprimé → `intervention.technicien = NULL`

### Intégrations externes
- **CRM Service**: `Client.crm_id` → Tiers CRM
- **Auth Service**: User IDs dans les logs d'audit
- **File Storage**: Photos et documents

---

## ⚠️ Règles de Validation

### Logique métier
1. **Statuts**: Transitions autorisées uniquement :
   - `PLANIFIEE` → `EN_COURS` ou `ANNULEE`
   - `EN_COURS` → `TERMINEE` ou `ANNULEE`
   - `TERMINEE` → Aucune transition
   - `ANNULEE` → Aucune transition

2. **Dates cohérentes**: 
   - `date_debut` ≥ `date_planifiee`
   - `date_fin` ≥ `date_debut`
   - `date_planifiee` future (créations)

3. **Coûts**: Tous ≥ 0, mis à jour automatiquement

4. **Multi-tenant**: `tenant_id` obligatoire, filtrage automatique

### Contraintes techniques
- Tous les IDs sont des entiers auto-incrémentés
- UUIDs pour `tenant_id` et `crm_id`
- Dates au format ISO 8601 avec timezone

---

## 📝 Exemples d'utilisation

### Créer une intervention
```http
POST /api/interventions/
Content-Type: application/json

{
  "titre": "Réparation chaudière urgente",
  "description": "Chaudière ne démarre plus, client sans chauffage",
  "client": 1,
  "priorite": "URGENTE",
  "date_planifiee": "2025-08-07T14:00:00Z",
  "duree_estimee_minutes": 180,
  "cout_main_oeuvre": 200.00,
  "tenant_id": "tenant-abc-123"
}
```

### Démarrer une intervention
```http
POST /api/interventions/1/demarrer/
Content-Type: application/json

{
  "date_debut": "2025-08-07T14:15:00Z"
}
```

### Ajouter du matériel
```http
POST /api/interventions/1/materials/
Content-Type: application/json

{
  "nom": "Joint étanchéité 20mm",
  "quantite": 2,
  "prix_unitaire": 15.50
}
```

### Créer un rapport
```http
POST /api/interventions/1/reports/
Content-Type: application/json

{
  "contenu": "Intervention réalisée avec succès.\n\nProblème identifié: Joint défaillant sur circuit principal.\nAction réalisée: Remplacement joint + test étanchéité.\nRésultat: Chaudière opérationnelle, pression normale.\n\nClient satisfait, aucune réclamation."
}
```

---

## 🎯 Points d'attention Frontend

### Gestion d'état des interventions
- Utilisez les endpoints d'action pour changer les statuts
- Les transitions illégales retournent HTTP 400
- `date_debut` et `date_fin` sont auto-assignées par les actions

### Nested Resources
- Les tâches, matériaux, rapports, photos sont toujours liés à une intervention
- URLs imbriquées : `/api/interventions/{id}/tasks/`
- L'`intervention_id` est automatiquement assigné

### Upload de photos
```javascript
// FormData pour upload de fichiers
const formData = new FormData();
formData.append('image', file);
formData.append('description', 'Photo avant intervention');

fetch('/api/interventions/1/photos/', {
  method: 'POST',
  body: formData
})
```

### Filtrage et recherche
Paramètres disponibles :
- `?statut=EN_COURS` - Filtrer par statut
- `?priorite=URGENTE` - Filtrer par priorité  
- `?technicien=2` - Interventions d'un technicien
- `?date_planifiee_after=2025-08-07` - À partir d'une date
- `?search=chaudière` - Recherche full-text (titre + description)
- `?ordering=-date_planifiee` - Tri par date (- pour desc)

### Pagination
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/interventions/?page=2",
  "previous": null,
  "results": [...]
}
```

### Format des réponses d'erreur
```json
{
  "detail": "Transition non autorisée",
  "code": "invalid_transition",
  "field_errors": {
    "statut": ["Ne peut pas passer de TERMINEE à EN_COURS"]
  }
}
```

---

**Généré automatiquement à partir des modèles Django**  
**Date**: 2025-08-07  
**Équipe Backend**: Service Intervention