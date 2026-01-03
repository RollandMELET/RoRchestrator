# Feature: Dashboard Traçabilité

## Contexte
Voir `_context.md` pour le contexte complet du projet GS1 France.

## Dépendances
Cette feature **dépend de** :
- ✅ `api-lookup` : API produits doit être disponible
- ✅ `batch-import` : Produits doivent pouvoir être importés

## Objectif
Créer une interface Hotwire pour visualiser et gérer les flux de produits.

## Spécifications

### 1. Controller Dashboard

Créer `app/controllers/dashboard_controller.rb` :

```ruby
class DashboardController < ApplicationController
  def index
    @total_products = Product.count
    @products_with_valid_gtin = Product.with_valid_gtin.count
    @recent_products = Product.order(created_at: :desc).limit(10)
  end
end
```

### 2. Vue Hotwire

Créer `app/views/dashboard/index.html.erb` :

**Sections requises :**
- KPIs (nombre produits, % GTIN valides)
- Liste des produits récents (Turbo Frame)
- Formulaire de recherche par GTIN
- Statistiques par fabricant (graphique simple)

**Utiliser :**
- Turbo Frames pour le contenu dynamique
- Stimulus controllers pour les interactions
- Tailwind CSS pour le styling

### 3. Routes

Ajouter à `config/routes.rb` :

```ruby
root "dashboard#index"

resources :dashboard, only: [:index]
```

### 4. Stimulus Controller

Créer `app/javascript/controllers/product_search_controller.js` :

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input", "results"]

  async search() {
    const gtin = this.inputTarget.value

    if (!gtin) return

    const response = await fetch(`/api/v1/products/${gtin}`)
    const data = await response.json()

    // Afficher le résultat dans Turbo Frame
    // ...
  }
}
```

### 5. Tests

Créer `spec/controllers/dashboard_controller_spec.rb` et `spec/system/dashboard_spec.rb` :

**Tests controller :**
- ✅ GET /dashboard → 200 OK
- ✅ Variables d'instance assignées

**Tests système (avec Capybara) :**
- ✅ Page affiche les KPIs
- ✅ Recherche par GTIN fonctionne
- ✅ Liste des produits s'affiche

## Contraintes techniques

- Utiliser Hotwire (Turbo + Stimulus)
- Pas de React ni Vue.js
- API calls via Fetch API
- Styling avec Tailwind CSS
- Responsive (mobile-first)

## Critères de succès

- [ ] `bundle exec rspec spec/controllers/dashboard_controller_spec.rb` passe
- [ ] `bundle exec rspec spec/system/dashboard_spec.rb` passe
- [ ] Interface accessible sur `http://localhost:3000/dashboard`
- [ ] Recherche GTIN temps réel < 500ms
- [ ] Design responsive et moderne

## Fichiers à créer/modifier

- `app/controllers/dashboard_controller.rb` (nouveau)
- `app/views/dashboard/index.html.erb` (nouveau)
- `app/javascript/controllers/product_search_controller.js` (nouveau)
- `config/routes.rb` (modifier)
- `spec/controllers/dashboard_controller_spec.rb` (nouveau)
- `spec/system/dashboard_spec.rb` (nouveau)

## Design requis

- Header avec logo GS1
- Navigation simple
- Cards pour les KPIs (style moderne)
- Table produits avec tri
- Formulaire de recherche avec feedback visuel
- Footer avec infos projet
