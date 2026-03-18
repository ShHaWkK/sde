# Modeles d'Embedding — Choisir le bon

> L'embedding, c'est la "traduction" du texte en nombres. Le choix du modele
> determine la precision du diff et les contraintes (taille, vitesse, cout, offline).

---

## Comprendre les embeddings en 30 secondes

```
"Le vendeur doit livrer."  --------> [0.23, -0.14, 0.87, ...]  384 nombres
                                              |
"The vendor must deliver." --------> [0.24, -0.13, 0.85, ...]  <- tres proche !
                                              |
"Le chien aboie."         --------> [0.89, 0.42, -0.11, ...]  <- loin
```

Le modele a appris que des phrases semantiquement equivalentes, meme
dans des langues differentes, doivent produire des vecteurs proches.

---

## Comparaison des modeles disponibles

```
+---------------------------+-------+--------+--------+---------+----------+
| Modele                    | Dim.  | Taille | Vitesse| Offline | Cout     |
+---------------------------+-------+--------+--------+---------+----------+
| all-MiniLM-L6-v2 (defaut) |  384  |  80MB  | ~1ms   |   Oui   | Gratuit  |
| all-mpnet-base-v2         |  768  | 420MB  | ~5ms   |   Oui   | Gratuit  |
| text-embedding-3-small    | 1536  |   -    | ~100ms |   Non   | $0.02/1M |
| text-embedding-3-large    | 3072  |   -    | ~150ms |   Non   | $0.13/1M |
| ollama:nomic-embed-text   |  768  | ~270MB | ~10ms  |   Oui   | Gratuit  |
+---------------------------+-------+--------+--------+---------+----------+
                                              (CPU, par chunk)
```

---

## Modele par defaut : `all-MiniLM-L6-v2`

```bash
semantic-diff diff a.txt b.txt  # utilise all-MiniLM-L6-v2 par defaut
```

Le meilleur compromis vitesse/precision pour la plupart des cas :
- Telecharge automatiquement au premier lancement (~80MB)
- Tourne sur CPU sans GPU
- Entraine specifiquement sur des taches de similarite semantique
- Supporte 50+ langues

---

## Meilleure precision : `all-mpnet-base-v2`

```bash
semantic-diff diff a.txt b.txt --model all-mpnet-base-v2
```

Quand la precision compte plus que la vitesse (contrats longs, analyse medicale).

```
MiniLM  : ░░░░░░░░░░ vitesse  ████████ precision
mpnet   : ░░░░ vitesse        ██████████ precision
```

---

## OpenAI : `text-embedding-3-small`

```bash
OPENAI_API_KEY=sk-... semantic-diff diff a.txt b.txt --model text-embedding-3-small
```

Le meilleur en precision absolue, mais necessite une cle API et une connexion.

```
Quand l'utiliser :
  - Pipelines de production ou la precision est critique
  - Documents legaux ou medicaux a fort enjeu
  - Budget API disponible

Quand ne pas l'utiliser :
  - Environnements offline / air-gapped
  - Volume eleve (cout peut devenir significatif)
  - Besoin de determinisme total (les modeles OpenAI evoluent)
```

---

## Ollama (local) : `ollama:nomic-embed-text`

```bash
# 1. Installer Ollama : https://ollama.ai
# 2. Telecharger le modele
ollama pull nomic-embed-text

# 3. Utiliser avec SDE
semantic-diff diff a.txt b.txt --model ollama:nomic-embed-text
```

La solution **privacy-first** : tout reste sur ta machine, aucune donnee envoyee.

```
Cas d'usage ideaux :
  - Donnees sensibles (santé, droit, finance)
  - Environnements sans acces internet
  - Reglementation RGPD stricte
```

---

## Guide de choix rapide

```
Tu traites des donnees sensibles ou n'as pas internet ?
  -> ollama:nomic-embed-text

Tu veux le meilleur sans te prendre la tete ?
  -> all-MiniLM-L6-v2  (defaut)

Tu as besoin de la meilleure precision possible ?
  -> all-mpnet-base-v2  (local)
  -> text-embedding-3-small (si API disponible)

Tes textes sont multilingues ?
  -> paraphrase-multilingual-MiniLM-L12-v2
     (ajouter --model paraphrase-multilingual-MiniLM-L12-v2)

Tu fais des benchmarks / comparaisons de modeles ?
  -> semantic-diff benchmark --model <nom>
     Les resultats s'ajoutent automatiquement a benchmarks/leaderboard.json
```

---

## Ajouter un nouveau backend

Implementer `AbstractEmbedder` dans `core/models/` :

```python
# core/models/mon_modele.py
import numpy as np
from .base import AbstractEmbedder

class MonModeleEmbedder(AbstractEmbedder):

    def __init__(self, model_name: str):
        self._model_name = model_name
        # charger le modele ici

    @property
    def model_name(self) -> str:
        return self._model_name

    def encode(self, texts: list[str]) -> np.ndarray:
        # retourner un array (N, dim)
        ...
```

Puis l'enregistrer dans `core/models/__init__.py` dans la factory `get_embedder()`.
