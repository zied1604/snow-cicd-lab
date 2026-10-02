# snow-cicd-lab v1

[![deploy](https://github.com/ton-pseudo/snow-cicd-lab/actions/workflows/deploy.yml/badge.svg)](https://github.com/ton-pseudo/snow-cicd-lab/actions/workflows/deploy.yml)
[![pr-checks](https://github.com/ton-pseudo/snow-cicd-lab/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/ton-pseudo/snow-cicd-lab/actions/workflows/pr-checks.yml)

---

## Table des matieres

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture et stack technique](#2-architecture-et-stack-technique)
3. [Structure du depot](#3-structure-du-depot)
4. [Strategie de branches et flux de promotion](#4-strategie-de-branches-et-flux-de-promotion)
5. [Convention de nommage des branches](#5-convention-de-nommage-des-branches)
6. [Prerequis et configuration locale](#6-prerequis-et-configuration-locale)
7. [Configuration Snowflake](#7-configuration-snowflake)
8. [Configuration des secrets GitHub](#8-configuration-des-secrets-github)
9. [Workflows GitHub Actions](#9-workflows-github-actions)
10. [Projet dbt](#10-projet-dbt)
11. [Qualite du code — pre-commit](#11-qualite-du-code--pre-commit)
12. [Guide de contribution](#12-guide-de-contribution)

---

## 1. Vue d'ensemble

**snow-cicd-lab** est un laboratoire de reference CI/CD pour des projets de transformation de donnees bases sur **Snowflake** et **dbt**.

L'objectif est de demontrer une pipeline GitOps complete et industrialisee, couvrant :

- la validation automatique du code (lint Python, lint SQL, scan de secrets)
- le deploiement progressif via des environnements isoles (`dev` → `uat` → `prod`)
- la creation d'environnements CI **ephemeres** par pull request
- l'application stricte des regles de promotion et de nommage des branches
- l'authentification securisee a Snowflake via cle privee RSA (sans mot de passe)

Ce depot peut servir de base ou de modele pour tout projet Data Engineering professionnel cible sur Snowflake.

---

## 2. Architecture et stack technique

| Composant | Outil / Version |
|---|---|
| Data warehouse | Snowflake |
| Framework de transformation | dbt-core + dbt-snowflake |
| CI/CD | GitHub Actions |
| Lint Python | Ruff |
| Tests Python | pytest |
| Lint SQL | SQLFluff (dialecte Snowflake) |
| Scan de secrets | Gitleaks |
| Pre-commit hooks | pre-commit |
| Python | 3.11+ |
| Gestion des dependances Python | pip + `requirements.txt` |
| Dependabot | Mises a jour auto (GitHub Actions + pip) |

### Environnements Snowflake

```
ANALYTICS_DEV   ← cible du target dbt "dev" (feature branches, CI ephemere)
ANALYTICS_UAT   ← cible du target dbt "uat"
ANALYTICS_PROD  ← cible du target dbt "prod" (branche main uniquement)
```

---

## 3. Structure du depot

```
snow-cicd-lab/
├── .github/
│   ├── workflows/
│   │   ├── branch-name-check.yml   # Valide le nom de la branche source d'une PR
│   │   ├── ci-cleanup.yml          # Supprime le schema CI ephemere a la fermeture d'une PR
│   │   ├── deploy.yml              # Deploiement dbt sur dev / uat / prod
│   │   ├── pr-checks.yml           # Controles qualite sur les PR (lint, tests, dbt CI)
│   │   └── promotion-guard.yml     # Applique la sequence de promotion dev → uat → main
│   ├── CODEOWNERS                  # Proprietaires de code par repertoire
│   ├── dependabot.yml              # Mises a jour automatiques des dependances
│   └── pull_request_template.md    # Template de description de PR
├── dbt/
│   ├── macros/
│   │   ├── drop_ci_schema.sql      # Macro de nettoyage des schemas CI ephemeres
│   │   └── generate_schema_name.sql # Override du nom de schema (logique CI/cible)
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_customers.sql   # Modele de staging des clients
│   │   └── schema.yml              # Documentation et tests des modeles
│   ├── seeds/
│   │   └── customers.csv           # Donnees de reference (clients exemples)
│   ├── dbt_project.yml             # Configuration du projet dbt
│   ├── packages.yml                # Dependances dbt (dbt_utils)
│   └── profiles.yml                # Profils de connexion Snowflake par environnement
├── python/
│   ├── src/
│   │   └── utils.py                # Fonctions utilitaires Python
│   └── tests/
│       └── test_utils.py           # Tests unitaires pytest
├── sql/                            # Scripts SQL additionnels
├── .gitignore
├── .pre-commit-config.yaml         # Configuration des hooks pre-commit
├── .sqlfluff                       # Configuration SQLFluff
├── pyproject.toml                  # Configuration ruff et pytest
└── requirements.txt                # Dependances Python du projet
```

---

## 4. Strategie de branches et flux de promotion

Le projet suit un modele **GitFlow simplifie** avec trois branches permanentes :

```
feature/fix/chore/...
         │
         ▼
        dev  ──────────────────────────────► ANALYTICS_DEV
         │
         ▼
        uat  ──────────────────────────────► ANALYTICS_UAT
         │
         ▼
        main ──────────────────────────────► ANALYTICS_PROD

        hotfix/* ──► uat ou main directement (bypass dev autorise)
```

### Regles de promotion (appliquees automatiquement par `promotion-guard.yml`)

| PR vers | Branche source autorisee |
|---|---|
| `uat` | `dev` ou `hotfix/*` |
| `main` | `uat` ou `hotfix/*` |

De plus, toute PR vers `main` exige que le **dernier deploiement de la branche `uat` soit en succes** avant d'etre mergee.

---

## 5. Convention de nommage des branches

Le workflow `branch-name-check.yml` valide automatiquement le nom de chaque branche source d'une PR.

### Format obligatoire

```
<type>/<TICKET>-<description-courte>
```

| Champ | Valeurs acceptees | Exemple |
|---|---|---|
| `type` | `feature`, `fix`, `hotfix`, `chore`, `docs`, `refactor` | `feature` |
| `TICKET` | Lettres majuscules + chiffres, tiret, numero | `PROJ-123` |
| `description` | Mots en minuscules separes par des tirets | `ajout-modele-clients` |

**Exemples valides :**

```
feature/PROJ-123-ajout-modele-clients
fix/DATA-42-correction-type-date
hotfix/OPS-7-prod-schema-manquant
chore/INFRA-15-mise-a-jour-deps
docs/WIKI-3-readme-initial
refactor/CORE-88-renommer-colonnes
```

**Branches exemptees** (pas de validation) : `dev`, `uat`, `main`, `dependabot/*`

---

## 6. Prerequis et configuration locale

### 6.1 Outils requis

- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **Git 2.x+**
- **pre-commit** — gestionnaire de hooks Git
- **Acces Snowflake** — compte, role, warehouse, bases configures (voir section 7)

### 6.2 Installation de l'environnement

```bash
# 1. Cloner le depot
git clone https://github.com/ton-pseudo/snow-cicd-lab.git
cd snow-cicd-lab

# 2. Creer et activer un environnement virtuel Python
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows

# 3. Installer les dependances Python
pip install -r requirements.txt

# 4. Installer les hooks pre-commit
pre-commit install

# 5. Installer les packages dbt
dbt deps --project-dir dbt
```

### 6.3 Variables d'environnement requises en local

Creer un fichier `.env` (non versionne) ou exporter les variables dans le terminal :

```bash
export SNOWFLAKE_ACCOUNT="<orgname>-<accountname>"   # ex: myorg-myaccount
export SNOWFLAKE_USER="CICD_USER"
export SNOWFLAKE_PRIVATE_KEY_PATH="/chemin/vers/rsa_key.p8"
```

---

## 7. Configuration Snowflake

### 7.1 Creer les objets Snowflake necessaires

Se connecter a Snowflake avec un role `SYSADMIN` / `SECURITYADMIN` et executer :

```sql
-- Creer le role CI/CD
USE ROLE SECURITYADMIN;
CREATE ROLE IF NOT EXISTS CICD_ROLE;

-- Creer l'utilisateur de service (authentification par cle, sans mot de passe)
CREATE USER IF NOT EXISTS CICD_USER
    DEFAULT_ROLE    = CICD_ROLE
    DEFAULT_WAREHOUSE = CICD_WH
    COMMENT         = 'Utilisateur de service pour la pipeline CI/CD';

GRANT ROLE CICD_ROLE TO USER CICD_USER;

-- Creer le warehouse
USE ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS CICD_WH
    WAREHOUSE_SIZE  = 'X-SMALL'
    AUTO_SUSPEND    = 60
    AUTO_RESUME     = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT         = 'Warehouse dedie au CI/CD';

GRANT USAGE ON WAREHOUSE CICD_WH TO ROLE CICD_ROLE;

-- Creer les bases de donnees par environnement
CREATE DATABASE IF NOT EXISTS ANALYTICS_DEV  COMMENT = 'Environnement de developpement';
CREATE DATABASE IF NOT EXISTS ANALYTICS_UAT  COMMENT = 'Environnement de recette';
CREATE DATABASE IF NOT EXISTS ANALYTICS_PROD COMMENT = 'Environnement de production';

-- Accorder les privileges au role CICD_ROLE
GRANT ALL PRIVILEGES ON DATABASE ANALYTICS_DEV  TO ROLE CICD_ROLE;
GRANT ALL PRIVILEGES ON DATABASE ANALYTICS_UAT  TO ROLE CICD_ROLE;
GRANT ALL PRIVILEGES ON DATABASE ANALYTICS_PROD TO ROLE CICD_ROLE;

GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE ANALYTICS_DEV  TO ROLE CICD_ROLE;
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE ANALYTICS_UAT  TO ROLE CICD_ROLE;
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE ANALYTICS_PROD TO ROLE CICD_ROLE;
```

### 7.2 Generer la paire de cles RSA (authentification sans mot de passe)

```bash
# 1. Generer la cle privee (PKCS#8, chiffree AES-256)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# 2. Extraire la cle publique
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# 3. Afficher la cle publique (pour la coller dans Snowflake)
cat rsa_key.pub
```

### 7.3 Associer la cle publique a l'utilisateur Snowflake

```sql
-- Remplacer <CONTENU_CLE_PUBLIQUE> par le contenu entre
-- les lignes -----BEGIN PUBLIC KEY----- et -----END PUBLIC KEY-----
ALTER USER CICD_USER SET RSA_PUBLIC_KEY = '<CONTENU_CLE_PUBLIQUE>';

-- Verifier l'association
DESC USER CICD_USER;
```

> **Securite :** Ne jamais commiter la cle privee (`rsa_key.p8`) dans le depot.
> Ajouter `*.p8` et `*.pem` au `.gitignore`.

---

## 8. Configuration des secrets GitHub

Les workflows GitHub Actions consomment les secrets suivants. Ils doivent etre configures **par environnement** dans les parametres du depot :
`Settings > Environments > <env> > Secrets`.

| Environnement GitHub | Secret | Description |
|---|---|---|
| `dev`, `uat`, `prod` | `SNOWFLAKE_ACCOUNT` | Identifiant du compte Snowflake (ex: `myorg-myaccount`) |
| `dev`, `uat`, `prod` | `SNOWFLAKE_USER` | Nom de l'utilisateur de service (ex: `CICD_USER`) |
| `dev`, `uat`, `prod` | `SNOWFLAKE_PRIVATE_KEY` | Contenu complet du fichier `rsa_key.p8` (avec les lignes d'en-tete) |

> **Note :** L'environnement `prod` correspond a la branche `main`. Le workflow `deploy.yml` fait
> automatiquement la correspondance `main → prod`.

---

## 9. Workflows GitHub Actions

### Vue d'ensemble

| Workflow | Fichier | Declencheur | Role |
|---|---|---|---|
| PR Checks | `pr-checks.yml` | PR ouverte vers `dev`, `uat`, `main` | Lint, tests, scan secrets, dbt CI |
| Deploy | `deploy.yml` | Push sur `dev`, `uat`, `main` | Deploiement dbt sur l'environnement cible |
| CI Cleanup | `ci-cleanup.yml` | Fermeture d'une PR | Supprime le schema Snowflake CI ephemere |
| Branch Name Check | `branch-name-check.yml` | PR ouverte/mise a jour | Valide le nom de la branche source |
| Promotion Guard | `promotion-guard.yml` | PR vers `uat` ou `main` | Valide la sequence de promotion |

---

### 9.1 `pr-checks.yml` — Controles qualite sur les PR

Ce workflow orchestre **4 jobs paralleles** (sauf `dbt-ci` qui depend des lints) :

```
lint-python ──┐
              ├──► dbt-ci
lint-sql ─────┘

secrets-scan (independant)
```

| Job | Outil | Ce qu'il verifie |
|---|---|---|
| `lint-python` | ruff + pytest | Style, imports, formatage Python ; tests unitaires |
| `lint-sql` | SQLFluff | Style et syntaxe des modeles SQL dbt |
| `secrets-scan` | Gitleaks | Absence de secrets ou tokens dans le diff |
| `dbt-ci` | dbt build | Compilation et tests dbt dans un schema isole `CI_PR_<numero>` |

Le job `dbt-ci` utilise le target `ci` du fichier `profiles.yml` et cree automatiquement un schema
Snowflake isole nomme `CI_PR_<numero_de_PR>` dans la base `ANALYTICS_DEV`.

---

### 9.2 `deploy.yml` — Deploiement dbt

Declenche automatiquement apres chaque push sur une branche permanente.

| Branche | Target dbt | Base Snowflake |
|---|---|---|
| `dev` | `dev` | `ANALYTICS_DEV` |
| `uat` | `uat` | `ANALYTICS_UAT` |
| `main` | `prod` | `ANALYTICS_PROD` |

Le workflow utilise `concurrency` pour **annuler un deploiement en cours** si un nouveau push
arrive sur la meme branche.

---

### 9.3 `ci-cleanup.yml` — Nettoyage des schemas ephemeres

A la fermeture (merge ou abandon) d'une PR, ce workflow appelle la macro dbt `drop_ci_schema`
pour supprimer le schema `CI_PR_<numero>` de `ANALYTICS_DEV`.

Cela garantit que **chaque PR dispose d'un environnement propre et isole**, sans accumulation
de schemas obsoletes dans Snowflake.

---

### 9.4 `branch-name-check.yml` — Convention de nommage

Valide que la branche source d'une PR respecte le format :
`(feature|fix|hotfix|chore|docs|refactor)/PROJ-123-description`.

Si le nom est invalide, la PR est bloquee avec un message d'erreur explicite.

---

### 9.5 `promotion-guard.yml` — Garde de promotion

Garantit que le code suit toujours le chemin `dev → uat → main`.

- Toute PR vers `main` depuis une autre branche que `uat` (ou `hotfix/*`) est rejetee.
- Toute PR vers `uat` depuis une autre branche que `dev` (ou `hotfix/*`) est rejetee.
- En plus, pour les PR vers `main`, le **dernier deploiement de `uat` doit etre en succes**.

---

## 10. Projet dbt

### 10.1 Profils et cibles

Le fichier `dbt/profiles.yml` definit quatre cibles :

| Target | Usage | Base Snowflake | Schema |
|---|---|---|---|
| `dev` | Developpement local et branche `dev` | `ANALYTICS_DEV` | `STG_ANALYTICS` |
| `ci` | Chaque PR (CI ephemere) | `ANALYTICS_DEV` | `CI_PR_<numero>` |
| `uat` | Branche `uat` | `ANALYTICS_UAT` | `STG_ANALYTICS` |
| `prod` | Branche `main` | `ANALYTICS_PROD` | `STG_ANALYTICS` |

### 10.2 Modeles

| Modele | Type | Description |
|---|---|---|
| `stg_customers` | table | Staging des clients : normalisation du pays en majuscules, renommage des colonnes |

**Tests automatiques configures (`schema.yml`) :**
- `customer_id` : `not_null`, `unique`
- `country` : `not_null`

### 10.3 Seeds

| Fichier | Contenu |
|---|---|
| `seeds/customers.csv` | Jeu de donnees exemples (clients) utilise pour les tests CI |

### 10.4 Macros

| Macro | Role |
|---|---|
| `generate_schema_name` | Override de la logique dbt de nommage de schema. En cible `ci`, le schema cible est utilise tel quel (sans prefixe). |
| `drop_ci_schema` | Supprime un schema Snowflake via `DROP SCHEMA IF EXISTS`. Appelee par le workflow `ci-cleanup`. |

### 10.5 Commandes dbt utiles

```bash
# Installer les packages dbt
dbt deps --project-dir dbt

# Charger les seeds
dbt seed --project-dir dbt --target dev

# Executer les modeles
dbt run --project-dir dbt --target dev

# Lancer les tests
dbt test --project-dir dbt --target dev

# Compiler + tester en une commande (equivalent CI)
dbt build --project-dir dbt --target dev

# Supprimer un schema CI manuellement
dbt run-operation drop_ci_schema --project-dir dbt --target ci \
  --args "{schema_name: CI_PR_99}"
```

---

## 11. Qualite du code — pre-commit

Le projet utilise **pre-commit** pour appliquer automatiquement les regles de qualite avant chaque commit.

### Hooks configures

| Hook | Outil | Ce qu'il fait |
|---|---|---|
| `ruff` | Ruff | Lint Python (style, imports, bugs courants) |
| `ruff-format` | Ruff | Formatage automatique du code Python |
| `sqlfluff-lint` | SQLFluff | Lint des fichiers SQL (dialecte Snowflake) |
| `gitleaks` | Gitleaks | Detection de secrets, tokens, cles dans les fichiers commites |

### Installation et utilisation

```bash
# Installer les hooks dans le depot Git local
pre-commit install

# Executer manuellement sur tous les fichiers
pre-commit run --all-files

# Mettre a jour les versions des hooks
pre-commit autoupdate
```

### Configuration SQLFluff (`.sqlfluff`)

```ini
[sqlfluff]
dialect          = snowflake
templater        = jinja
max_line_length  = 120
exclude          = dbt/target, dbt/dbt_packages
```

### Configuration Ruff (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B"]   # pycodestyle, pyflakes, isort, bugbear
```

---

## 12. Guide de contribution

### Flux de travail standard

```
1. Creer une branche depuis dev
   git checkout dev && git pull
   git checkout -b feature/PROJ-123-ma-fonctionnalite

2. Developper et commiter
   git add .
   git commit -m "feat: description claire du changement"
   # Les hooks pre-commit s'executent automatiquement

3. Ouvrir une Pull Request vers dev
   - Remplir le template de PR
   - Attendre que les 4 jobs de pr-checks soient verts

4. Apres merge dans dev → ouvrir une PR dev → uat
   - Le promotion-guard verifie la source

5. Apres validation en UAT → ouvrir une PR uat → main
   - Le dernier deploiement UAT doit etre en succes
```

### Checklist PR (tiree du template)

- [ ] Tests dbt ajoutes ou mis a jour (`not_null`, `unique`, `relationships`)
- [ ] Pas de `SELECT *` ni de donnees en dur dans les modeles
- [ ] Modele documente dans `schema.yml` (description + colonnes)
- [ ] Impact sur les couts du warehouse evalue
- [ ] Aucune donnee sensible ni secret dans le diff
- [ ] Plan de retour arriere (rollback) decrit si le changement est risque

### Proprietes du code (CODEOWNERS)

| Repertoire | Proprietaire |
|---|---|
| `/dbt/models/` | @ton-pseudo |
| `/sql/` | @ton-pseudo |
| `/.github/` | @ton-pseudo |
| `*` (tout le reste) | @ton-pseudo |

---

## Licence

Ce projet est un laboratoire a des fins pedagogiques et de demonstration.
