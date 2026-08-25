# Phone-Medic

Outil **multiplateforme** (Windows, macOS, Linux, Termux/Android) en Python : diagnostic d'appareil Android, assistant mode développeur + débogage USB, récupération de téléphone semi-briqué via fastboot/firmwares officiels, et volet carte SIM (verrouillage opérateur, déblocage légitime, eSIM).

## Installation

```bash
# Python 3 requis, puis les outils Android :
# Windows : winget install Google.PlatformTools
# macOS   : brew install --cask android-platform-tools
# Linux   : sudo apt install adb fastboot
# Termux  : pkg install android-tools

python3 phonemedic.py
```

## Ce que l'outil FAIT

| Fonction | Menu | Condition |
|---|---|---|
| Diagnostic complet (modèle, batterie, bootloader, débogage USB) | 1 | Téléphone démarre |
| Guide pas-à-pas adapté à votre marque (Samsung, Xiaomi, Huawei…) pour activer développeur + débogage USB | 2 | Tactile fonctionnel OU souris OTG branchée |
| Redémarrage vers bootloader/recovery, état du bootloader | 3 | Semi-brique OK |
| Déverrouillage bootloader (efface tout) + flash d'images officielles | 3 | Votre appareil |
| Réinitialisation usine fastboot | 3 | — |
| Liens firmwares officiels selon marque (Odin, MiFlash, Pixel images…) | 3 | — |
| Test verrouillage opérateur, procédure officielle de déblocage SIM, eSIM | 4 | OS démarré |
| **Occasion bloqué FRP + SIM étrangère** : solution officielle (retrait à distance du compte Google par le vendeur), vérif IMEI/blacklist, codes de déblocage opérateurs US, lettre type en anglais pour le vendeur, recours PayPal/eBay | 6 | — |

## Ce qu'AUCUN logiciel ne peut faire (limites physiques)

- **Téléphone totalement éteint / mort** : le mode développeur et le débogage USB sont des réglages *de l'OS Android*. Si l'OS ne démarre pas, rien n'est modifiable par logiciel. Chargez 30 min, forcez redémarrage (Vol− + Power 10 s), sinon → réparation matérielle.
- **Contournement universel des verrous** (écran verrouillé, FRP, compte Google d'autrui) : non fourni. Passez par les canaux officiels : Find My Device (Google), Samsung Find My Mobile, service constructeur avec preuve d'achat.
- **Lecteur SIM cassé** : panne matérielle, seule la réparation du lecteur aide.
- **eSIM sans l'opérateur** : les profils eSIM ne s'installent que via l'app/QR de l'opérateur (sécurité matérielle).

## Déblocage SIM légitime (résumé)

1. IMEI via `*#06#`.
2. Opérateur d'origine = responsable du déblocage ; gratuit dans l'UE après 3–6 mois (règlement UE 2015/2120).
3. Import : constructeur avec preuve d'achat.

## Légal / éthique

N'utilisez ces outils que sur **vos propres appareils** ou avec l'autorisation explicite du propriétaire. Le déverrouillage du bootloader efface toutes les données et peut annuler la garantie.
