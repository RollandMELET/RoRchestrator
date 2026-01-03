# Feature: Import Batch CSV

## Contexte
Voir `_context.md` pour le contexte complet du projet GS1 France.

## Dépendances
Cette feature **dépend de** :
- ✅ `auth-gtin` : Product#valid_gtin? doit être disponible

## Objectif
Implémenter un système d'import de produits depuis fichiers CSV au format GS1.

## Spécifications

### 1. Service BatchImporter

Créer `app/services/batch_importer.rb` :

```ruby
class BatchImporter
  def initialize(csv_file_path)
    @csv_path = csv_file_path
    @errors = []
    @imported = 0
    @skipped = 0
  end

  # Importe le CSV et retourne les stats
  def import!
    CSV.foreach(@csv_path, headers: true) do |row|
      import_row(row)
    end

    {
      imported: @imported,
      skipped: @skipped,
      errors: @errors
    }
  end

  private

  def import_row(row)
    gtin = row['gtin']
    name = row['name']

    # Validation
    unless Product.new(gtin: gtin).valid_gtin?
      @errors << "Ligne #{row.lineno}: GTIN invalide #{gtin}"
      @skipped += 1
      return
    end

    # Créer ou mettre à jour
    product = Product.find_or_initialize_by(gtin: gtin)
    product.update!(name: name, ...)
    @imported += 1
  rescue => e
    @errors << "Ligne #{row.lineno}: #{e.message}"
    @skipped += 1
  end
end
```

### 2. Format CSV attendu

```csv
gtin,name,description,manufacturer
1234567890128,Produit A,Description du produit A,Fabricant X
9876543210982,Produit B,Description du produit B,Fabricant Y
```

### 3. Rake Task

Créer `lib/tasks/import.rake` :

```ruby
namespace :gs1 do
  desc "Import products from CSV file"
  task :import_products, [:file_path] => :environment do |t, args|
    importer = BatchImporter.new(args[:file_path])
    stats = importer.import!

    puts "Import terminé:"
    puts "  Importés: #{stats[:imported]}"
    puts "  Ignorés: #{stats[:skipped]}"

    if stats[:errors].any?
      puts "\nErreurs:"
      stats[:errors].each { |e| puts "  - #{e}" }
    end
  end
end
```

### 4. Tests RSpec

Créer `spec/services/batch_importer_spec.rb` :

**Cas de tests requis :**
- ✅ Import d'un CSV valide avec 3 produits
- ✅ Import avec certains GTIN invalides (skip)
- ✅ Import avec produits déjà existants (update)
- ❌ Fichier CSV inexistant
- ✅ CSV avec headers manquants

## Contraintes techniques

- Utiliser la gem CSV native de Ruby
- Utiliser `Product#valid_gtin?` pour validation
- Transaction par ligne (pas de rollback global)
- Logging des erreurs détaillé

## Critères de succès

- [ ] `bundle exec rspec spec/services/batch_importer_spec.rb` passe
- [ ] `rake gs1:import_products[test.csv]` fonctionne
- [ ] Import de 100 produits < 10 secondes
- [ ] Gestion des doublons (update au lieu d'erreur)

## Fichiers à créer/modifier

- `app/services/batch_importer.rb` (nouveau)
- `lib/tasks/import.rake` (nouveau)
- `spec/services/batch_importer_spec.rb` (nouveau)
- `spec/fixtures/files/sample_products.csv` (nouveau)

## Exemple de test manuel

```bash
# Créer un CSV de test
cat > test_products.csv << EOF
gtin,name,description
1234567890128,Test Product 1,Description 1
9876543210982,Test Product 2,Description 2
EOF

# Lancer l'import
bundle exec rake gs1:import_products[test_products.csv]
```
