#!/bin/bash
# RoRchestrator - Wrapper global pour orchestration parallèle de Claude Code
#
# Ce script installe automatiquement RoRchestrator dans le projet courant
# et lance orchestrate.py avec les arguments fournis.
#
# Usage:
#   rorchestrator plan
#   rorchestrator run --yes
#   rorchestrator cleanup --merged
#   rorchestrator status

set -e  # Exit on error

# Configuration
RORCHESTRATOR_SOURCE="/Users/rollandmelet/Développement/Projets/RoRchestrator"
RORCHESTRATOR_VERSION="1.0.0"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions helper
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Vérifier que le source existe
if [ ! -d "$RORCHESTRATOR_SOURCE" ]; then
    print_error "Source RoRchestrator introuvable: $RORCHESTRATOR_SOURCE"
    print_info "Vérifiez que 101EvolutionLab/orchestrator existe"
    exit 1
fi

# Vérifier qu'on est dans un repo Git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Vous n'êtes pas dans un repo Git"
    print_info "RoRchestrator nécessite un repo Git pour fonctionner"
    print_info "Initialisez un repo avec: git init"
    exit 1
fi

# Installer RoRchestrator si absent
if [ ! -d "orchestrator" ]; then
    echo ""
    print_info "RoRchestrator n'est pas installé dans ce projet"
    print_info "Installation en cours..."
    echo ""

    # Copier depuis le source et renommer en "orchestrator"
    cp -r "$RORCHESTRATOR_SOURCE" orchestrator

    print_success "RoRchestrator installé (version $RORCHESTRATOR_VERSION)"
    echo ""
    print_warning "Configuration requise :"
    echo "  1. Éditer orchestrator/config/feature_list.json"
    echo "  2. Créer les prompts dans orchestrator/prompts/"
    echo "  3. Lancer: rorchestrator plan"
    echo ""

    # Si pas d'arguments, s'arrêter ici pour laisser l'utilisateur configurer
    if [ $# -eq 0 ]; then
        print_info "RoRchestrator installé. Configurez avant utilisation."
        exit 0
    fi
fi

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que Claude Code est disponible
if ! command -v claude &> /dev/null; then
    print_warning "Claude Code CLI n'est pas dans le PATH"
    print_info "Vérifiez avec: which claude"
fi

# Lancer orchestrate.py avec les arguments
cd orchestrator
exec python3 orchestrate.py "$@"
