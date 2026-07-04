# Sangha Virtuelle

Application web simple de méditations guidées (HTML, CSS, JavaScript purs, sans framework).

Pour ajouter une séance : ouvrez `content/sessions.json`, ajoutez un fichier audio dans `audio/`, puis ajoutez un objet dans le tableau `sessions` sur le même modèle que la séance de test.

## Ajouter une séance chaque semaine (automatique)

Une seule fois : lancez `bash setup-cle.sh` dans votre terminal pour enregistrer votre clé API ElevenLabs (elle reste uniquement sur votre machine, dans `.env`, jamais sur GitHub).

Chaque semaine :
1. Modifiez `contenu-semaine/texte.txt` avec le texte de la nouvelle méditation.
2. Modifiez `contenu-semaine/meta.json` avec les infos de la séance (id, titre, theme, duree, description).
3. Lancez : `python3 generer-audio.py`

Le script génère l'audio, met à jour `content/sessions.json`, puis commit et pousse sur GitHub automatiquement.

### Ajouter des silences dans le texte

Par défaut, le texte s'enchaîne sans pause. Pour insérer un vrai silence à un endroit précis (par exemple pour laisser le temps de se recentrer), écrivez `[pause N]` sur sa propre ligne, où `N` est le nombre de secondes :

```
Une phrase de l'instruction.
[pause 10]
La phrase suivante, après 10 secondes de silence.
```

Vous pouvez utiliser n'importe quel nombre de secondes (entier ou décimal, ex. `[pause 2.5]`).

### Changer la voix

Le script utilise par défaut une voix "Antoni". Pour en utiliser une autre : allez dans votre compte ElevenLabs → Voice Library, choisissez une voix, copiez son Voice ID, puis ajoutez (ou modifiez) dans `.env` la ligne `ELEVENLABS_VOICE_ID=xxxxx`.
