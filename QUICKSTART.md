# Quick Start - RoRchestrator

Démarrage rapide en 5 minutes.

## Installation (30 secondes)

```bash
cd /path/to/votre-projet
cp -r /path/to/orchestrator .
cd orchestrator
```

**Prérequis :** Python 3.9+, Git, Claude Code CLI

## Configuration (2 minutes)

### 1. Éditer feature_list.json

```bash
cp config/feature_list.example.json config/feature_list.json
nano config/feature_list.json
```

Modifier :
- `project.name` : Nom de votre projet
- `project.repo_path` : Chemin vers le repo Git (`.` si dans le repo)
- `project.base_branch` : Branche de base (`main`, `master`, `develop`)
- `features` : Liste de vos features

### 2. Créer les prompts

Pour chaque feature, créer `prompts/{feature-id}.md` :

```markdown
# Feature: {Nom}

## Objectif
Ce que doit faire la feature.

## Spécifications
- Spéc 1
- Spéc 2

## Critères de succès
- [ ] Tests passent
- [ ] Code fonctionne
```

## Utilisation (2 minutes)

### Voir le plan

```bash
python3 orchestrate.py plan
```

Vérifiez :
- ✅ Pas d'erreurs de dépendances
- ✅ Ordre d'exécution correct
- ✅ Speedup intéressant

### Lancer l'exécution

```bash
python3 orchestrate.py run
```

Confirmez avec `o` quand demandé.

### Attendre la fin

L'orchestrateur affiche :
```
[14:30] 🚀 feature-a: started
[14:32] ✅ feature-a: completed
[14:32] 🚀 feature-b: started
[14:32] 🚀 feature-c: started  ← PARALLÈLE
...
```

### Voir le rapport

À la fin, un rapport s'affiche :
```
RAPPORT D'EXÉCUTION

Features   : 4
  ✅ Succès : 4
  ❌ Échecs : 0

Coût total : $2.47
Speedup    : 1.3x

Branches créées :
  • feature/feature-a
  • feature/feature-b
```

### Review et merge

```bash
# Aller dans un worktree
cd ../worktrees/feature-a

# Review le code
code .
git diff master

# Si OK, merger
cd /path/to/repo
git checkout main
git merge feature/feature-a
git push
```

### Cleanup

Après merge :

```bash
cd orchestrator
python3 orchestrate.py cleanup --merged
```

---

## Commandes Essentielles

```bash
# Aide générale
python3 orchestrate.py --help

# Aide d'une commande
python3 orchestrate.py run --help

# Plan (dry-run)
python3 orchestrate.py plan

# Status du projet
python3 orchestrate.py status

# Exécuter avec confirmation
python3 orchestrate.py run

# Exécuter sans confirmation (CI/CD)
python3 orchestrate.py run --yes

# Cleanup worktrees mergés
python3 orchestrate.py cleanup --merged

# Cleanup TOUT (attention!)
python3 orchestrate.py cleanup --all

# Tests (développeurs)
python3 -m unittest discover tests -v

# Démos
python3 demo_dag.py
python3 demo_worktree.py
python3 demo_integrated.py
```

---

## Template Minimal

```json
{
  "project": {
    "name": "MonProjet",
    "repo_path": ".",
    "base_branch": "main"
  },
  "claude": {
    "permission_mode": "acceptEdits",
    "allowed_tools": ["Read", "Write", "Edit"]
  },
  "features": [
    {
      "id": "feature-1",
      "name": "Ma première feature",
      "depends_on": [],
      "prompt_file": "feature-1.md"
    }
  ]
}
```

---

## Exemple Complet

Voir `config/feature_list.example.json` pour :
- Configuration complète d'un projet Rails
- 4 features avec dépendances
- Estimations de tokens
- Métadonnées (creates, uses, tags)

---

## En Cas de Problème

### Claude CLI introuvable

```bash
which claude           # Doit afficher un chemin
claude --version       # Doit fonctionner
```

### Erreur de dépendance

```bash
python3 orchestrate.py plan
# ❌ Feature 'B' dépend de features inexistantes: ['A']
```

→ Vérifier les IDs dans `depends_on`

### Worktree existe déjà

```bash
python3 orchestrate.py cleanup --all
```

Puis relancer.

---

## Pour Aller Plus Loin

- **Guide complet :** `GUIDE-UTILISATION.md`
- **Documentation technique :** `README.md`
- **Analyse complète :** `../analyses/2026-01-02-rorchestrator-documentation.md`

---

**Temps total de setup + première exécution : ~5 minutes**
