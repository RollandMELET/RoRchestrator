# Guide d'Utilisation - RoRchestrator

Guide pratique pour utiliser RoRchestrator dans vos projets.

## Installation

### Prérequis

- Python 3.9+ (utilise uniquement la stdlib, pas de dépendances externes)
- Git installé
- Claude Code CLI installé et dans le PATH

### Vérification

```bash
python3 --version     # Doit être >= 3.9
git --version
claude --version      # Claude Code CLI
```

### Setup

```bash
# Cloner ou copier RoRchestrator dans votre projet
cp -r /path/to/orchestrator /path/to/votre-projet/

cd /path/to/votre-projet/orchestrator

# Vérifier que tout fonctionne
python3 orchestrate.py --help
```

## Configuration

### 1. Créer feature_list.json

Copier le template :

```bash
cp config/feature_list.example.json config/feature_list.json
```

Éditer `config/feature_list.json` :

```json
{
  "project": {
    "name": "MonProjet",
    "repo_path": "..",              // Chemin vers le repo Git
    "base_branch": "main",          // Branche de base
    "max_parallel": 3,              // Max 3 features en parallèle
    "timeout_seconds": 1800         // 30 min par feature
  },
  "claude": {
    "permission_mode": "acceptEdits",
    "allowed_tools": [
      "Read", "Write", "Edit",
      "Bash(npm test)"
    ]
  },
  "features": [
    {
      "id": "feature-a",
      "name": "Feature A",
      "description": "...",
      "depends_on": [],             // Pas de dépendances
      "prompt_file": "feature-a.md",
      "estimated_tokens": 30000
    },
    {
      "id": "feature-b",
      "name": "Feature B",
      "depends_on": ["feature-a"],  // Attend que feature-a soit faite
      "prompt_file": "feature-b.md",
      "estimated_tokens": 20000
    }
  ]
}
```

### 2. Créer les prompts

Pour chaque feature, créer un fichier dans `prompts/` :

**prompts/feature-a.md :**
```markdown
# Feature A

## Objectif
Description claire de ce que doit faire la feature.

## Spécifications
- Détail 1
- Détail 2

## Critères de succès
- [ ] Tests passent
- [ ] Code documenté
```

**Conseil** : Créer un `prompts/_context.md` avec le contexte projet commun.

## Workflow Standard

### Étape 1 : Planification

Afficher le plan d'exécution :

```bash
python3 orchestrate.py plan
```

**Sortie :**
```
PLAN D'EXÉCUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 4 features en 3 vagues

VAGUE 1
  │ feature-a ← aucune dépendance

VAGUE 2 [PARALLÈLE]
  │ feature-b ← attend ['feature-a']
  │ feature-c ← attend ['feature-a']

VAGUE 3
  │ feature-d ← attend ['feature-b', 'feature-c']

💰 Tokens estimés: 120,000
⚡ Speedup théorique: 1.3x
```

Vérifier que :
- ✅ Pas d'erreurs de dépendances
- ✅ L'ordre d'exécution est correct
- ✅ Le speedup est intéressant

### Étape 2 : Vérification de l'état

```bash
python3 orchestrate.py status
```

**Sortie :**
```
STATUT DU PROJET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Projet : MonProjet
📂 Repo   : /path/to/repo
🌿 Branche: main
📊 Features: 4
🤖 Claude CLI: ✅ disponible
```

### Étape 3 : Exécution

#### Avec confirmation

```bash
python3 orchestrate.py run
```

Vous serez invité à confirmer :
```
Lancer l'exécution ? [o/N] : o
```

#### Sans confirmation (CI/CD)

```bash
python3 orchestrate.py run --yes
```

#### Progression temps réel

Pendant l'exécution, vous verrez :

```
VAGUE 1 - 1 feature(s)
  [14:30:15] 🚀 feature-a: started
  [14:32:45] ✅ feature-a: completed

VAGUE 2 - 2 feature(s)
  [14:32:46] 🚀 feature-b: started
  [14:32:46] 🚀 feature-c: started
  [14:35:20] ✅ feature-b: completed
  [14:36:10] ✅ feature-c: completed
```

### Étape 4 : Review des résultats

Après l'exécution, un rapport est affiché :

```
RAPPORT D'EXÉCUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Projet         : MonProjet
Durée totale   : 12.5 minutes (temps CPU)
Durée réelle   : 6.3 minutes (wall time)
Coût total     : $2.47

Features       : 4
  ✅ Succès     : 4
  ❌ Échecs     : 0

Branches créées :
  • feature/feature-a
  • feature/feature-b
  • feature/feature-c
  • feature/feature-d

⚡ Speedup: 1.98x
```

Les rapports sont aussi sauvegardés :
- `reports/report_20260102_143045.json`
- `reports/results_20260102_143045.json`

### Étape 5 : Review du code

Les worktrees sont créés dans `../worktrees/` :

```bash
# Lister les worktrees
cd ..
ls worktrees/

# Review une feature
cd worktrees/feature-a
code .

# Voir les changements
git diff master
```

### Étape 6 : Merge

#### Via GitHub (recommandé)

```bash
# Pour chaque branche réussie
cd worktrees/feature-a
git push origin feature/feature-a

# Créer une PR sur GitHub
gh pr create --title "feat: Feature A" --body "..."
```

#### Merge local

```bash
cd /path/to/repo

git checkout main
git merge feature/feature-a
git push
```

### Étape 7 : Cleanup

Après avoir mergé, nettoyer les worktrees :

```bash
python3 orchestrate.py cleanup --merged
```

**Sortie :**
```
🧹 Nettoyage des worktrees mergés...
✅ 4 worktrees nettoyés:
  • feature-a
  • feature-b
  • feature-c
  • feature-d
```

Pour tout nettoyer (attention !) :

```bash
python3 orchestrate.py cleanup --all
```

## Cas d'Usage Avancés

### Debugging une feature

Si une feature échoue :

```bash
# 1. Voir l'erreur dans le rapport
cat reports/results_*.json | grep -A 5 '"success": false'

# 2. Aller dans le worktree
cd ../worktrees/feature-problematique

# 3. Investiguer
git log
git status

# 4. Corriger manuellement ou relancer Claude
claude -p "Fix the error: ..."

# 5. Commiter
git add .
git commit -m "fix: resolve issue"
```

### Exécution séquentielle (debugging)

Pour exécuter une feature à la fois (utile pour debugging) :

```bash
python3 orchestrate.py run --sequential
```

Désactive le parallélisme, exécute dans l'ordre topologique.

### Ajouter une feature après coup

1. Éditer `config/feature_list.json`
2. Ajouter la nouvelle feature
3. Relancer `orchestrate.py plan` pour vérifier
4. Exécuter

### Utiliser un autre repo

```bash
# Option 1: modifier feature_list.json
"repo_path": "/path/to/autre/repo"

# Option 2: créer une config séparée
cp config/feature_list.json config/autre-projet.json
python3 orchestrate.py plan --config config/autre-projet.json
```

## Bonnes Pratiques

### 1. Granularité des features

✅ **Bonne granularité :**
```json
{
  "id": "user-auth",
  "name": "User authentication with JWT",
  "estimated_tokens": 30000
}
```

❌ **Trop large :**
```json
{
  "id": "complete-backend",
  "name": "Build entire backend",
  "estimated_tokens": 500000
}
```

**Règle :** Une feature = 1-2 heures de dev Claude max (~50k tokens)

### 2. Déclaration des dépendances

Utilisez les champs `creates` et `uses` pour aider à identifier les dépendances :

```json
{
  "id": "auth",
  "creates": ["UserAuth class", "authenticate! method"]
},
{
  "id": "api",
  "depends_on": ["auth"],
  "uses": ["authenticate! method"]
}
```

### 3. Gestion des fichiers partagés

Si deux features touchent le même fichier (ex: `routes.rb`), soit :
- Les rendre séquentielles avec `depends_on`
- Les fusionner en une seule feature

### 4. Estimation des tokens

Pour estimer :
- Feature simple (CRUD) : ~20-30k tokens
- Feature avec API externe : ~40-50k tokens
- Feature UI complexe : ~50-80k tokens
- Feature avec tests complets : +20% tokens

### 5. Limites de parallélisme

**Recommandé :**
- `max_parallel: 3` pour machines puissantes (M4, etc.)
- `max_parallel: 2` pour machines standard
- `max_parallel: 1` si rate limits API posent problème

## Dépannage

### "Claude CLI n'est pas disponible"

```bash
# Vérifier l'installation
which claude
claude --version

# Si absent, installer Claude Code
# Voir: https://claude.ai/code
```

### "Erreur création worktree"

Vérifier que :
- Le repo_path est correct
- La branche de base existe
- Pas de worktrees orphelins (`git worktree prune`)

### "JSON parse error"

Le output de Claude n'est pas du JSON valide. Causes possibles :
- Version de Claude Code trop ancienne
- Option `--output-format json` non supportée
- Erreur dans le prompt qui fait planter Claude

### Feature timeout après 30 minutes

Soit :
- Augmenter `timeout_seconds` dans la config
- Découper la feature en plus petites parties
- Simplifier le prompt

## Exemples Complets

### Projet Rails

Voir `config/feature_list.example.json` pour un exemple complet d'un module Rails GS1.

### Projet Node.js/React

```json
{
  "project": {
    "name": "MyReactApp",
    "repo_path": "/Users/me/myapp",
    "base_branch": "develop",
    "max_parallel": 3
  },
  "claude": {
    "allowed_tools": [
      "Read", "Write", "Edit",
      "Bash(npm test)",
      "Bash(npm run lint)"
    ]
  },
  "features": [
    {
      "id": "setup-vite",
      "prompt_file": "setup-vite.md",
      "depends_on": []
    },
    {
      "id": "header-component",
      "prompt_file": "header.md",
      "depends_on": ["setup-vite"]
    }
  ]
}
```

## Logs et Rapports

Tous les rapports sont sauvegardés dans `reports/` :

```bash
reports/
├── report_20260102_143045.json   # Rapport d'exécution
└── results_20260102_143045.json  # Résultats détaillés par feature
```

Format JSON pour analyse ultérieure, intégration CI/CD, ou métriques.

## Intégration CI/CD

Exemple GitHub Actions :

```yaml
name: Parallel Features

on: workflow_dispatch

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Claude Code
        run: |
          # Installation de Claude Code
          # ...

      - name: Run RoRchestrator
        run: |
          cd orchestrator
          python3 orchestrate.py run --yes

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: execution-reports
          path: orchestrator/reports/
```

## Support

Pour plus d'informations :
- Documentation complète : `../analyses/2026-01-02-rorchestrator-documentation.md`
- Tests unitaires : `tests/test_*.py`
- Scripts de démo : `demo_*.py`
