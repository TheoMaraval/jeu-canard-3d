#!/usr/bin/env bash
# Régénère tout le pipeline pour les villes données (par défaut : toutes).
#   bash blender/tout_generer.sh            # props + les quatre villes + aperçus
#   bash blender/tout_generer.sh lille      # une seule ville (props compris)
# BLENDER peut pointer vers l'exécutable si blender n'est pas dans le PATH.
# L'index assets/scenes.json n'est jamais supprimé : chaque ville y met à jour sa ligne.
set -u
cd "$(dirname "$0")/.."
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.3/blender.exe}"
filtre='Traceback|Error|  File|RESULTAT|DIAGNOSTIC|Impossible|gabarit'

python -m unittest discover -s blender/tests -t blender 2>&1 | tail -1
"$B" --background --python blender/build_assets.py 2>&1 | grep -E "$filtre" | cut -c1-200
"$B" --background --python blender/build_kit.py 2>&1 | grep -E "$filtre|assert" | cut -c1-200
villes=("$@")
[ ${#villes[@]} -eq 0 ] && villes=(paris new_york lille delhi)
for v in "${villes[@]}"; do
  echo "=== $v"
  "$B" --background --python blender/build_quartier.py -- --ville "$v" 2>&1 | grep -E "$filtre"
  "$B" --background "blender/scenes/$v.blend" --python blender/place_objets.py -- --ville "$v" 2>&1 | grep -E "$filtre"
  "$B" --background "blender/scenes/$v.blend" --python blender/render_ville.py -- --ville "$v" 2>&1 | grep -E "$filtre"
done
