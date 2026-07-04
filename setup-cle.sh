#!/bin/bash
# =========================================================
# setup-cle.sh
# Ce script vous demande votre clé API ElevenLabs et l'enregistre
# dans le fichier .env, à la racine du projet.
#
# IMPORTANT : lancez ce script vous-même depuis VOTRE terminal
# (Terminal.app ou le terminal intégré de VS Code), jamais via
# l'assistant, pour que la clé ne soit jamais visible dans le chat.
#
# Utilisation : bash setup-cle.sh
# =========================================================

# On se place dans le dossier où se trouve ce script, quel que soit
# l'endroit d'où on le lance, pour être sûr d'écrire le .env au bon endroit
cd "$(dirname "$0")"

# "read -s" masque la saisie à l'écran, comme un mot de passe
read -s -p "Collez votre clé API ElevenLabs puis appuyez sur Entrée : " CLE
echo

if [ -z "$CLE" ]; then
  echo "Aucune clé saisie, rien n'a été enregistré."
  exit 1
fi

# On écrit la clé dans .env, au format attendu par generer-audio.py
echo "ELEVENLABS_API_KEY=$CLE" > .env

# On restreint la lecture du fichier à vous seul, par sécurité
chmod 600 .env

echo "Clé enregistrée dans .env (fichier ignoré par Git, jamais poussé sur GitHub)."
