#!/usr/bin/env python3
# =========================================================
# generer-audio.py
#
# Ce script automatise l'ajout d'une nouvelle séance chaque semaine :
# 1. Il lit le texte à lire dans contenu-semaine/texte.txt
# 2. Il lit les informations de la séance dans contenu-semaine/meta.json
# 3. Il appelle l'API ElevenLabs pour transformer le texte en audio (voix française)
# 4. Il sauvegarde l'audio dans audio/
# 5. Il ajoute (ou met à jour) la séance dans content/sessions.json
# 6. Il fait un commit Git et le pousse sur GitHub
#
# N'utilise que la bibliothèque standard de Python : aucune installation
# de paquet externe n'est nécessaire.
#
# Utilisation : python3 generer-audio.py
# =========================================================

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

# Dossier où se trouve ce script : on s'en sert comme racine du projet,
# pour que le script fonctionne quel que soit l'endroit d'où il est lancé.
RACINE = os.path.dirname(os.path.abspath(__file__))

# Identifiant de voix ElevenLabs utilisé par défaut si aucun n'est précisé
# dans le .env (voix "Antoni" : masculine, chaleureuse et posée).
# Vous pouvez le changer en ajoutant une ligne ELEVENLABS_VOICE_ID=... dans .env
VOIX_PAR_DEFAUT = "ErXwobaYiN019PkySvjV"


def charger_env():
    """Lit le fichier .env à la main (ligne par ligne) et renvoie un dictionnaire.
    On évite volontairement toute dépendance externe comme python-dotenv."""
    chemin_env = os.path.join(RACINE, ".env")
    variables = {}

    if not os.path.exists(chemin_env):
        return variables

    with open(chemin_env, "r", encoding="utf-8") as fichier:
        for ligne in fichier:
            ligne = ligne.strip()
            # On ignore les lignes vides ou les commentaires (qui commencent par #)
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            variables[cle.strip()] = valeur.strip()

    return variables


def lire_meta():
    """Charge les informations de la séance (id, titre, theme, duree, description)."""
    chemin = os.path.join(RACINE, "contenu-semaine", "meta.json")
    with open(chemin, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def lire_texte():
    """Charge le texte complet à transformer en audio."""
    chemin = os.path.join(RACINE, "contenu-semaine", "texte.txt")
    with open(chemin, "r", encoding="utf-8") as fichier:
        return fichier.read().strip()


def ajouter_pauses(texte):
    """Transforme les marqueurs [pause N] écrits dans texte.txt en vrais silences de N secondes.

    Exemple à écrire dans contenu-semaine/texte.txt :
        Une phrase de l'instruction.
        [pause 10]
        La phrase suivante, après 10 secondes de silence.

    ElevenLabs limite chaque balise de pause à 3 secondes (au-delà, la voix
    devient instable) : pour une pause de 10 secondes, on enchaîne donc
    plusieurs balises de 3 secondes maximum jusqu'à atteindre le total demandé.
    En dehors de ces marqueurs, le texte s'enchaîne normalement : c'est vous
    qui décidez où et combien de temps durent les silences."""

    def remplacer_par_balises(correspondance):
        secondes_restantes = float(correspondance.group(1))
        balises = []
        while secondes_restantes > 0:
            duree = min(secondes_restantes, 3.0)
            balises.append('<break time="{:.1f}s" />'.format(duree))
            secondes_restantes -= duree
        return " " + "".join(balises) + " "

    texte = re.sub(r"\[pause\s+([0-9]+(?:\.[0-9]+)?)\]", remplacer_par_balises, texte)

    # Les retours à la ligne restants (qui ne sont pas des [pause N]) sont
    # remplacés par un simple espace : ils ne créent pas de silence imposé
    texte = texte.replace("\n", " ")

    return texte


def generer_audio(texte, cle_api, voice_id):
    """Envoie le texte à l'API ElevenLabs et renvoie les octets du fichier audio (mp3)."""
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + voice_id

    corps_requete = json.dumps({
        "text": texte,
        # Modèle multilingue d'ElevenLabs : nécessaire pour une voix française de qualité
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            # Stabilité plutôt haute et peu d'exagération : convient à un ton posé,
            # adapté à de la méditation guidée plutôt qu'à une voix expressive
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }).encode("utf-8")

    requete = urllib.request.Request(url, data=corps_requete, method="POST")
    requete.add_header("xi-api-key", cle_api)
    requete.add_header("Content-Type", "application/json")
    requete.add_header("Accept", "audio/mpeg")

    with urllib.request.urlopen(requete) as reponse:
        return reponse.read()


def mettre_a_jour_sessions(meta, nom_fichier_audio):
    """Ajoute la séance dans content/sessions.json, ou la remplace si son id existe déjà."""
    chemin = os.path.join(RACINE, "content", "sessions.json")

    with open(chemin, "r", encoding="utf-8") as fichier:
        donnees = json.load(fichier)

    nouvelle_seance = {
        "id": meta["id"],
        "titre": meta["titre"],
        "theme": meta["theme"],
        "duree": meta["duree"],
        "audio": "audio/" + nom_fichier_audio,
        "description": meta["description"]
    }

    sessions = donnees["sessions"]
    deja_remplacee = False

    for index, seance in enumerate(sessions):
        if seance["id"] == meta["id"]:
            sessions[index] = nouvelle_seance
            deja_remplacee = True
            break

    if not deja_remplacee:
        sessions.append(nouvelle_seance)

    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, ensure_ascii=False, indent=2)
        fichier.write("\n")

    return deja_remplacee


def publier_sur_git(titre):
    """Ajoute les fichiers modifiés, crée un commit, puis pousse sur GitHub."""
    subprocess.run(["git", "add", "-A"], cwd=RACINE, check=True)

    message = "Ajout séance : " + titre
    resultat_commit = subprocess.run(["git", "commit", "-m", message], cwd=RACINE)

    if resultat_commit.returncode != 0:
        print("Rien à valider, ou erreur lors du commit (voir ci-dessus).")
        return

    resultat_push = subprocess.run(["git", "push"], cwd=RACINE)
    if resultat_push.returncode != 0:
        print("Le push a échoué (peut-être un problème de connexion GitHub).")
        print("Vous pouvez pousser manuellement depuis VS Code (bouton de synchronisation).")


def main():
    variables = charger_env()
    cle_api = variables.get("ELEVENLABS_API_KEY")

    if not cle_api:
        print("Clé API ElevenLabs introuvable.")
        print("Lancez d'abord, dans votre terminal : bash setup-cle.sh")
        sys.exit(1)

    voice_id = variables.get("ELEVENLABS_VOICE_ID", VOIX_PAR_DEFAUT)

    try:
        meta = lire_meta()
        texte = lire_texte()
    except FileNotFoundError as erreur:
        print("Fichier manquant :", erreur)
        print("Vérifiez que contenu-semaine/meta.json et contenu-semaine/texte.txt existent bien.")
        sys.exit(1)

    texte = ajouter_pauses(texte)

    print("Génération de l'audio pour la séance : " + meta["titre"] + " ...")

    try:
        audio_octets = generer_audio(texte, cle_api, voice_id)
    except urllib.error.HTTPError as erreur:
        detail = erreur.read().decode("utf-8", errors="ignore")
        print("Erreur renvoyée par l'API ElevenLabs (code " + str(erreur.code) + ") :")
        print(detail)
        sys.exit(1)

    nom_fichier = meta["id"] + ".mp3"
    chemin_audio = os.path.join(RACINE, "audio", nom_fichier)

    with open(chemin_audio, "wb") as fichier:
        fichier.write(audio_octets)

    print("Fichier audio enregistré : audio/" + nom_fichier)

    deja_remplacee = mettre_a_jour_sessions(meta, nom_fichier)
    if deja_remplacee:
        print("La séance existait déjà (même id) : elle a été mise à jour dans sessions.json.")
    else:
        print("Nouvelle séance ajoutée dans sessions.json.")

    publier_sur_git(meta["titre"])
    print("Terminé.")


if __name__ == "__main__":
    main()
