// =========================================================
// app.js
// Ce script fait deux choses :
// 1. Il va chercher la liste des séances dans content/sessions.json
//    et l'affiche dans le menu.
// 2. Il gère le lecteur audio (lecture, pause, barre de progression).
// =========================================================

// On récupère une bonne fois pour toutes les éléments du HTML dont on aura besoin
const vueMenu = document.getElementById("vue-menu");
const vueLecteur = document.getElementById("vue-lecteur");
const listeSeances = document.getElementById("liste-seances");
const boutonRetour = document.getElementById("bouton-retour");

const lecteurTitre = document.getElementById("lecteur-titre");
const lecteurTheme = document.getElementById("lecteur-theme");
const lecteurDescription = document.getElementById("lecteur-description");
const lecteurAudio = document.getElementById("lecteur-audio");
const lecteurMessage = document.getElementById("lecteur-message");

const boutonLecture = document.getElementById("bouton-lecture");
const barreProgression = document.getElementById("barre-progression");
const tempsEcoule = document.getElementById("temps-ecoule");

// On garde en mémoire si le fichier audio de la séance actuelle est utilisable
let audioDisponible = true;

// =========================================================
// Étape 1 : charger les séances depuis le fichier de données
// =========================================================

async function chargerSeances() {
  try {
    const reponse = await fetch("content/sessions.json");
    const donnees = await reponse.json();
    afficherMenu(donnees.sessions);
  } catch (erreur) {
    // Si le fichier est introuvable ou mal formé, on informe l'utilisateur
    // plutôt que de laisser la page vide sans explication.
    listeSeances.innerHTML = "<li>Impossible de charger les séances pour le moment.</li>";
    console.error("Erreur de chargement de content/sessions.json :", erreur);
  }
}

// Construit la liste affichée dans le menu à partir du tableau de séances
function afficherMenu(sessions) {
  listeSeances.innerHTML = "";

  sessions.forEach(function (seance) {
    const item = document.createElement("li");
    item.className = "seance-item";
    item.innerHTML =
      '<div class="seance-titre">' + seance.titre + "</div>" +
      '<div class="seance-meta">' + seance.theme + " · " + seance.duree + "</div>";

    // Au clic sur une séance, on ouvre le lecteur avec ses informations
    item.addEventListener("click", function () {
      ouvrirLecteur(seance);
    });

    listeSeances.appendChild(item);
  });
}

// =========================================================
// Étape 2 : le lecteur
// =========================================================

function ouvrirLecteur(seance) {
  // On remplit les informations textuelles de la séance
  lecteurTitre.textContent = seance.titre;
  lecteurTheme.textContent = seance.theme;
  lecteurDescription.textContent = seance.description;

  // On réinitialise l'état du lecteur avant de charger le nouvel audio
  audioDisponible = true;
  lecteurMessage.classList.add("cachee");
  boutonLecture.classList.remove("cachee");
  boutonLecture.textContent = "Lecture";
  barreProgression.value = 0;
  tempsEcoule.textContent = "0:00";

  // On donne la nouvelle source audio au lecteur
  lecteurAudio.src = seance.audio;

  // On bascule l'affichage : on cache le menu, on montre le lecteur
  vueMenu.classList.add("cachee");
  vueLecteur.classList.remove("cachee");
}

// Si le fichier audio indiqué dans sessions.json n'existe pas (ou ne se charge pas),
// le navigateur déclenche l'événement "error" sur la balise <audio>.
// Plutôt que de planter, on affiche simplement "Audio à venir".
lecteurAudio.addEventListener("error", function () {
  audioDisponible = false;
  lecteurMessage.classList.remove("cachee");
  boutonLecture.classList.add("cachee");
});

// Clic sur le bouton Lecture / Pause
boutonLecture.addEventListener("click", function () {
  if (!audioDisponible) {
    return;
  }

  if (lecteurAudio.paused) {
    lecteurAudio.play();
    boutonLecture.textContent = "Pause";
  } else {
    lecteurAudio.pause();
    boutonLecture.textContent = "Lecture";
  }
});

// Quand l'audio avance, on met à jour la barre de progression et le temps affiché
lecteurAudio.addEventListener("timeupdate", function () {
  if (lecteurAudio.duration > 0) {
    const pourcentage = (lecteurAudio.currentTime / lecteurAudio.duration) * 100;
    barreProgression.value = pourcentage;
  }
  tempsEcoule.textContent = formaterTemps(lecteurAudio.currentTime);
});

// Quand on déplace la barre de progression à la main, on déplace la lecture audio
barreProgression.addEventListener("input", function () {
  if (audioDisponible && lecteurAudio.duration > 0) {
    lecteurAudio.currentTime = (barreProgression.value / 100) * lecteurAudio.duration;
  }
});

// Quand la séance se termine, on remet le bouton sur "Lecture"
lecteurAudio.addEventListener("ended", function () {
  boutonLecture.textContent = "Lecture";
});

// Transforme un nombre de secondes en affichage "minutes:secondes" (ex : 1:05)
function formaterTemps(secondes) {
  const minutes = Math.floor(secondes / 60);
  const secondesRestantes = Math.floor(secondes % 60);
  const secondesAffichees = secondesRestantes < 10 ? "0" + secondesRestantes : secondesRestantes;
  return minutes + ":" + secondesAffichees;
}

// =========================================================
// Bouton retour au menu
// =========================================================

boutonRetour.addEventListener("click", function () {
  // On met en pause l'audio en cours avant de revenir au menu
  lecteurAudio.pause();
  boutonLecture.textContent = "Lecture";

  vueLecteur.classList.add("cachee");
  vueMenu.classList.remove("cachee");
});

// =========================================================
// Démarrage : on charge les séances dès que le script s'exécute
// =========================================================

chargerSeances();
