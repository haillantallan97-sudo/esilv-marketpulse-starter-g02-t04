# Bloomberg Field Mapping

Ce document décrit comment le futur fournisseur Bloomberg
(`src/providers/bloomberg_provider.py`, TD10) doit convertir les données
Bloomberg vers le **format canonique MarketPulse**, le même que celui produit
par le fournisseur Yahoo (`src/providers/yahoo_provider.py`).

Grâce à ce contrat commun, `src/analytics.py` (rendement, base 100,
performance relative) fonctionne sans modification, quelle que soit la source.

```
Yahoo Finance  ─┐
                ├─►  observations canoniques  ─►  analytics
Bloomberg      ─┘    date · ticker · open · high · low · close · volume
```

## 1. Objectif et modes autorisés

Le fournisseur Bloomberg a un seul rôle : **lire une série Bloomberg et la
renvoyer sous forme d'observations canoniques**. Il ne fait aucun calcul
financier.

| Mode | Source des données | Terminal Bloomberg requis | Statut |
|---|---|---|---|
| `APPROVED_SAMPLE` (par défaut) | JSON approuvé `data/sample/bloomberg_reference_sample.json` | Non | Utilisé en TD |
| `LIVE` | Connexion à un Terminal Bloomberg autorisé | Oui | Hook non implémenté : lève `NotImplementedError` |

Règles :

- `APPROVED_SAMPLE` est le mode reproductible : il fonctionne dans Codespaces
  sans accès Bloomberg.
- Le JSON approuvé déclare lui-même `"access_mode": "approved_sample"` et
  `"is_live_bloomberg_output": false`. Ses valeurs sont **pédagogiques**
  (reprises de `data/sample/prices.csv`) et ne sont **pas** des historiques
  Bloomberg certifiés.
- Aucune connexion `LIVE` réussie ne doit être simulée. Toute capture d'écran
  doit indiquer le mode réellement utilisé.
- Un mode inconnu doit lever `ValueError`.

Fichiers de référence présents dans le dépôt :

| Fichier | Rôle |
|---|---|
| `data/sample/bloomberg_reference_sample.json` | Entrée : séries au format Bloomberg (clés `*_value`) |
| `data/sample/bloomberg_reference_expected.json` | Sortie attendue : lignes canoniques (`rows`) à comparer au résultat de la normalisation |
| `data/sample/instruments.json` | Métadonnées de l'instrument et du benchmark |

## 2. Identifiants AAPL / SP500

Un même instrument porte des identifiants différents selon la source.
**Les observations canoniques utilisent toujours le ticker MarketPulse**,
jamais l'identifiant Bloomberg.

| Ticker MarketPulse (canonique) | Identifiant Bloomberg (`provider_identifier`) | Instrument | Rôle |
|---|---|---|---|
| `AAPL` | `AAPL US Equity` | Apple Inc. (action) | instrument |
| `SP500` | `SPX Index` | S&P 500 (indice) | benchmark |

Pour comparaison, côté Yahoo : `AAPL` → `AAPL`, `SP500` → `^GSPC`.

Conséquences pour l'implémentation :

- un dictionnaire `BLOOMBERG_IDENTIFIERS = {"AAPL": "AAPL US Equity", "SP500": "SPX Index"}` ;
- un ticker absent de ce dictionnaire doit lever `ValueError` ;
- la série est sélectionnée dans le JSON par sa clé `provider_identifier` ;
  si elle est introuvable, lever `ValueError`.

## 3. Correspondance des champs et types

### Structure du JSON source

```text
payload
├── sample_kind, provider_stage, access_mode, is_live_bloomberg_output, provenance, schema_note
└── series : liste
    └── série
        ├── role                 "instrument" | "benchmark"
        ├── canonical_ticker     "AAPL" | "SP500"
        ├── provider_identifier  "AAPL US Equity" | "SPX Index"
        └── observations : liste (21 par série dans l'échantillon)
            └── observation_date, open_value, high_value, low_value, close_value, volume_value
```

Remarque : comme le précise le `schema_note` du JSON, les clés `*_value` sont des
clés pédagogiques, **pas des mnémoniques Bloomberg officiels** (`PX_LAST`, etc.).

### Champs source → cible

| Champ source Bloomberg | Champ MarketPulse | Type cible | Conversion |
|---|---|---|---|
| `observation_date` | `date` | `str` (`AAAA-MM-JJ`) | Copié tel quel |
| `canonical_ticker` (niveau **série**) | `ticker` | `str` | Copié depuis la série, pas depuis l'observation |
| `open_value` | `open` | `float` | `float(...)` |
| `high_value` | `high` | `float` | `float(...)` |
| `low_value` | `low` | `float` | `float(...)` |
| `close_value` | `close` | `float` | `float(...)` |
| `volume_value` | `volume` | `int` | `int(...)` |

Chaque observation canonique contient **exactement ces 7 clés**. Les nombres
sont convertis explicitement : une valeur peut arriver sous forme de chaîne
(`"110.0"`), et `"100.0" + "10"` donnerait `"100.010"` au lieu d'un calcul.

## 4. Exemple fictif : brut → canonique

> **Données fictives.** Cet exemple illustre le contrat, ce n'est pas une
> extraction Bloomberg.

Observation brute (série `AAPL US Equity`, `canonical_ticker = "AAPL"`) :

```python
raw = {
    "observation_date": "2026-11-18",
    "open_value": "100.0",
    "high_value": "112.0",
    "low_value": "99.0",
    "close_value": "110.0",
    "volume_value": "1500",
}
```

Observation canonique :

```python
canonical = {
    "date": raw["observation_date"],          # "2026-11-18"
    "ticker": "AAPL",                         # ticker MarketPulse, pas "AAPL US Equity"
    "open": float(raw["open_value"]),         # 100.0
    "high": float(raw["high_value"]),         # 112.0
    "low": float(raw["low_value"]),           # 99.0
    "close": float(raw["close_value"]),       # 110.0
    "volume": int(raw["volume_value"]),       # 1500
}
```

Assertions de contrat :

```python
assert set(canonical) == {"date", "ticker", "open", "high", "low", "close", "volume"}
assert canonical["ticker"] == "AAPL"
assert canonical["date"] == "2026-11-18"
assert isinstance(canonical["close"], float)
assert isinstance(canonical["volume"], int)
```

### Exercice : corriger une mauvaise normalisation

```python
wrong = {
    "date": "2026-11-18",
    "ticker": "AAPL US Equity",  # erreur : identifiant Bloomberg au lieu du ticker interne
    "open": "100.0",             # erreur : str au lieu de float
    "high": 112.0,
    "low": 99.0,
    "close": 110.0,
    "volume": "1500",            # erreur : str au lieu de int
}
```

1. **Champs au mauvais type** : `open` (`str`, attendu `float`) et `volume` (`str`, attendu `int`).
2. **Ticker interne correct** : `AAPL`, et non `AAPL US Equity`.
3. **Trois assertions qui échouent** sur `wrong` :

   ```python
   assert wrong["ticker"] == "AAPL"               # AssertionError
   assert isinstance(wrong["open"], float)        # AssertionError
   assert isinstance(wrong["volume"], int)        # AssertionError
   ```

4. **Dictionnaire corrigé** :

   ```python
   fixed = {
       "date": "2026-11-18",
       "ticker": "AAPL",
       "open": 100.0,
       "high": 112.0,
       "low": 99.0,
       "close": 110.0,
       "volume": 1500,
   }
   assert set(fixed) == {"date", "ticker", "open", "high", "low", "close", "volume"}
   assert fixed["ticker"] == "AAPL"
   assert all(isinstance(fixed[k], float) for k in ("open", "high", "low", "close"))
   assert isinstance(fixed["volume"], int)
   ```

## 5. Vérifications et limites du mode LIVE

### Contrôles à implémenter avant la normalisation (TD10)

Chaque anomalie doit lever une `ValueError` au message explicite, plutôt qu'une
`KeyError` peu lisible :

| Anomalie | Comportement attendu |
|---|---|
| `canonical_ticker` absent | `ValueError` |
| Liste `observations` absente ou vide | `ValueError` |
| Un des 6 champs obligatoires manquant (ex. `close_value`) | `ValueError` qui nomme le champ manquant |
| Deux observations avec la même `observation_date` | `ValueError` qui nomme la date dupliquée |
| Ticker inconnu dans `BLOOMBERG_IDENTIFIERS` | `ValueError` |
| Série introuvable pour un `provider_identifier` | `ValueError` |
| Mode différent de `APPROVED_SAMPLE` / `LIVE` | `ValueError` |

### Vérification de conformité

La simple présence de `bloomberg_reference_expected.json` ne prouve rien. Il
faut **comparer les valeurs** : les lignes normalisées doivent être égales aux
`rows` du fichier `expected`, champ par champ. On n'affiche « matching »
qu'après cette comparaison effective, et on signale toute différence.

### Limites du mode LIVE

- `LIVE` est un **point d'extension non implémenté** : il lève `NotImplementedError`.
- Il exige un Terminal Bloomberg et une licence autorisés, indisponibles dans Codespaces.
- Les vrais champs Bloomberg (`PX_OPEN`, `PX_HIGH`, `PX_LOW`, `PX_LAST`,
  `PX_VOLUME`, etc.) devront être reliés aux 7 champs canoniques lorsque le
  mode `LIVE` sera activé. Le contrat de sortie, lui, reste identique.
- Ne jamais présenter les données `APPROVED_SAMPLE` comme des données `LIVE`.
