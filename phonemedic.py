#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import time

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
NC = "\033[0m"

IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")

BRAND_GUIDES = {
    "samsung": "Paramètres > A propos du telephone > Informations logicielles > toucher 7x 'Numero de version' > Retour > Options de developpeur > activer 'Debogage USB'",
    "xiaomi": "Parametres > A propos du telephone > toucher 7x 'Version MIUI/HyperOS' > Parametres supplementaires > Options developpeur > activer 'Debogage USB' (compte Mi requis sur certains modeles)",
    "huawei": "Parametres > A propos du telephone > toucher 7x 'Numero de build' > Systeme et mises a jour > Options developpeur > activer 'Debogage USB'",
    "oppo": "Parametres > A propos du telephone > Version > toucher 7x 'Numero de build' > Parametres supplementaires > Options developpeur > 'Debogage USB'",
    "vivo": "Parametres > A propos du telephone > toucher 7x 'Numero de build' (ou 'Version logicielle') > Options developpeur > 'Debogage USB'",
    "oneplus": "Parametres > A propos de l'appareil > toucher 7x 'Numero de build' > Systeme > Options developpeur > 'Debogage USB'",
    "motorola": "Parametres > A propos du telephone > toucher 7x 'Numero de build' > Systeme > Options developpeur > 'Debogage USB'",
    "google": "Parametres > A propos du telephone > toucher 7x 'Numero de build' > Systeme > Options developpeur > 'Debogage USB'",
}

FIRMWARE_LINKS = {
    "samsung": "SamFw Tool / Odin + firmware sur samfw.com ou sammobile.com (mode Download : Vol- + Vol+ + brancher USB)",
    "xiaomi": "MiFlash + firmware officiel sur xiaomifirmwareupdater.com (fastboot ROM .tgz)",
    "google": "https://developers.google.com/android/images (factory images officielles Pixel)",
    "oneplus": "https://www.oneplus.com/support/softwareupgrade ( Oxygen Updater / MSM Download Tool)",
    "motorola": "https://mirrors.lolinet.com/firmware/moto/ (Lenovo Rescue and Smart Assistant)",
    "nokia": "Nokia Online Update Tool ou reparation via HMD",
}


def log(msg):
    print(f"{GREEN}[+]{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{NC} {msg}")


def err(msg):
    print(f"{RED}[x]{NC} {msg}")


def title(msg):
    print(f"\n{CYAN}--- {msg} ---{NC}")


def run(args, timeout=30):
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=timeout
        ).stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def tool_ok(name):
    return shutil.which(name) is not None


def check_tools():
    missing = [t for t in ("adb", "fastboot") if not tool_ok(t)]
    if missing:
        err(f"Outils manquants : {', '.join(missing)}")
        print("  Windows  : winget install Google.PlatformTools   (ou dl.google.com/android/repository/platform-tools)")
        print("  macOS    : brew install --cask android-platform-tools")
        print("  Linux    : sudo apt install adb fastboot | dnf | pacman")
        print("  Termux   : pkg install android-tools")
        return False
    return True


def adb(*args):
    return run(["adb", *args])


def fastboot(*args):
    return run(["fastboot", *args], timeout=60)


def wait_device():
    print("\nBranchez le telephone en USB et attendez...")
    for _ in range(60):
        state = adb_state()
        if state:
            log(f"Appareil detecte en mode '{state}'")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print()
    err("Aucun appareil detecte apres 60s.")
    diagnose_failure()
    return False


def adb_state():
    out = adb("get-state").lower()
    for s in ("device", "recovery", "sideload", "bootloader", "unauthorized", "offline"):
        if s in out:
            return s
    return None


def getprop(prop):
    val = adb("-s", serial(), "shell", "getprop", prop) if serial() else adb("shell", "getprop", prop)
    return val.replace("\r", "").strip()


_SERIAL_CACHE = {"v": None}


def serial():
    if _SERIAL_CACHE["v"] is None:
        devs = [l.split("\t")[0] for l in adb("devices").splitlines()[1:] if "\tdevice" in l]
        _SERIAL_CACHE["v"] = devs[0] if len(devs) == 1 else ""
    return _SERIAL_CACHE["v"]


def diagnose_failure():
    print("""
CAUSES POSSIBLES :
 1. Telephone completement ETEINT ou mort      -> AUCUN logiciel ne peut agir.
    Reessayez apres 30 min de charge sur un chargeur secteur, cable different,
    ou faites reparer la batterie/connecteur. Le debogage USB ne peut JAMAIS
    etre active sur un OS qui ne demarre pas.
 2. Debogage USB jamais active                 -> suivez l'assistant (menu 2)
    des que le telephone redemarre, ou utilisez un souris OTG pour naviguer
    si le tactile est casse (adaptateur USB-C/USB -> souris).
 3. Fenetre 'Autoriser le debogage ?' pas validee -> rebranchez, validez sur
    l'ecran du telephone (cochez 'Toujours autoriser').
""")


def diagnose():
    title("Diagnostic appareil")
    state = adb_state()
    if not state:
        err("Aucun appareil ADB. Essayez le mode bootloader (menu 3).")
        diagnose_failure()
        return
    if state in ("unauthorized", "offline"):
        warn(f"Appareil {state} : validez l'autorisation RSA sur son ecran, puis retestez.")
        return
    info = {
        "Modele": ["ro.product.brand", "ro.product.model"],
        "Android": ["ro.build.version.release"],
        "Patch securite": ["ro.build.version.security_patch"],
        "Chiffrement": ["ro.crypto.state"],
        "Bootloader verifie": ["ro.boot.verifiedbootstate"],
    }
    for label, props in info.items():
        vals = [getprop(p) for p in props]
        print(f"  {label:20}: {' '.join(v for v in vals if v)}")
    batt = adb("shell", "dumpsys", "battery")
    level = next((l.split(":")[1].strip() for l in batt.splitlines() if "level" in l), "?")
    print(f"  {'Batterie':20}: {level}%")
    dev_opt = adb("shell", "settings", "get", "global", "development_settings_enabled")
    dbg = adb("shell", "settings", "get", "global", "adb_enabled")
    print(f"  {'Options developpeur':20}: {'ACTIVEES' if dev_opt == '1' else 'DESACTIVEES'}")
    print(f"  {'Debogage USB':20}: {'ACTIF' if dbg == '1' else 'INACTIF'}")


def guide_devmode():
    title("Assistant Mode developpeur + Debogage USB")
    brand = ""
    if adb_state() == "device":
        brand = getprop("ro.product.brand").lower()
        print(f"Marque detectee : {brand or '?'}")
    guide = BRAND_GUIDES.get(brand)
    print("\nETAPES SUR LE TELEPHONE :")
    print(f"  {guide or BRAND_GUIDES['google']}")
    print("\nENSUITE :")
    print("  1. Activez aussi 'Deverrouillage OEM' (si present) : necessaire pour flasher.")
    print("  2. Branchez en USB, une fenetre 'Autoriser le debogage USB ?' apparait.")
    print("  3. Cochez 'Toujours autoriser' puis OK.")
    if input("\nTerminé ? Tester la connexion maintenant ? [o/N] ").strip().lower() == "o":
        _SERIAL_CACHE["v"] = None
        if adb_state() == "device":
            log("Connexion ADB operationnelle !")
            diagnose()
        else:
            err("Pas encore connecte. Verifiez l'autorisation sur l'ecran du telephone.")


def recovery_menu():
    title("Recuperation appareil semi-brique")
    if not wait_device():
        return
    while True:
        print("""
 [1] Redemarrer en mode bootloader/fastboot
 [2] Etat du bootloader (deverrouille ?)
 [3] DEVERROUILLER le bootloader  (EFFACE TOUTES LES DONNEES !)
 [4] Flasher une partition avec une image officielle
 [5] Reinitialisation usine via fastboot
 [6] Firmware officiel pour votre marque (liens)
 [7] Redemarrer normalement
 [0] Retour""")
        c = input("Choix : ").strip()
        if c == "1":
            adb("reboot", "bootloader")
            log("Attente du mode bootloader...")
            time.sleep(5)
            print(fastboot("devices") or "(fastboot ne voit rien : installez les pilotes USB de votre marque)")
        elif c == "2":
            out = fastboot("flashing", "get_unlock_ability") + fastboot("oem", "device-info")
            print(out or "Reponse vide : certains constructeurs bloquent ces commandes.")
        elif c == "3":
            warn("ATTENTION : le deverrouillage efface TOUTES les donnees et peut annuler la garantie.")
            warn("Ne faites ca que sur VOTRE appareil.")
            if input("Confirmer (tapez OUI) : ") == "OUI":
                print(fastboot("flashing", "unlock") or fastboot("oem", "unlock"))
                warn("Validez la confirmation SUR L'ECRAN DU TELEPHONE s'il en affiche une.")
        elif c == "4":
            part = input("Partition a flasher (boot/system/recovery/vendor/dtbo...) : ").strip()
            img = input("Chemin du fichier image officiel (.img) : ").strip().strip('"')
            if part and img and os.path.exists(img):
                print(fastboot("flash", part, img))
                log("Flash termine." if "okay" in str(fastboot("flash", part, img)).lower() else "")
            else:
                err("Fichier introuvable ou partition vide.")
        elif c == "5":
            if input("Effacer toutes les donnees ? [o/N] ").strip().lower() == "o":
                fastboot("-w")
                log("Wipe effectue.")
        elif c == "6":
            b = getprop("ro.product.brand").lower() if adb_state() == "bootloader" else ""
            print(FIRMWARE_LINKS.get(b, "Cherchez '<marque> firmware officiel' + outil de flash dedie (Odin/MiFlash/RSA)."))
        elif c == "7":
            fastboot("reboot") or adb("reboot")
            return
        elif c == "0":
            return


def sim_menu():
    title("Carte SIM / operateur")
    if adb_state() != "device":
        warn("Telephone non accessible via ADB. Les fonctions SIM exigent que l'OS tourne.")
        return
    imei = adb("shell", "dumpsys", "iphonesubinfo")
    print(f"  IMEI (si accessible) : {imei.replace(chr(13), '') or 'non expose par Android (normal sans root)'}")
    locked = [l for l in adb("shell", "getprop").splitlines() if any(k in l.lower() for k in ("simlock", "networklock", "sim_lock"))]
    print(f"  Props simlock        : {locked or 'aucune info standardisee (la detection fiable passe par l\'operateur)'}")
    print("""
COMMENT SAVOIR SI LE TELEPHONE EST VERROUILLE OPERATEUR ?
  Inserez une SIM d'un AUTRE operateur :
    - 'Reseau non disponible' / code demande -> verrouille.
    - Il capte -> deja debloque.

DEBLOCAGE OFFICIEL (legitime et souvent gratuit) :
  1. Notez votre IMEI : composez *#06# sur le telephone.
  2. Si achete chez un operateur : demandez le deblocage a CET operateur.
     Obligatoire et gratuit dans l'UE apres 3-6 mois (reglement (UE) 2015/2120).
     USA : T-Mobile/Metro via leur app ; AT&T sur att.com ; Verizon = non verrouille depuis 2020ish.
  3. Si importe : demandez au vendeur/constructeur avec preuve d'achat.
  4. Entrez le code recu quand une SIM etrangere est inseree.

ESIM :
  - L'activation eSIM se fait UNIQUEMENT via l'app/Qr de votre operateur
    (Parametres > Reseau > Ajouter un operateur / eSIM). Aucune app tierce
    ne peut installer un profil eSIM : c'est verrouille par securite.

LECTEUR SIM CASSE (carte non detectee sur aucun telephone) :
  -> Panne MATERIELLE. Reparation du lecteur necessaire, aucun logiciel n'y change rien.
""")


def dead_phone_info():
    print(f"""
{CYAN}=== TELEPHONE ETEINT / NE DEMARRE PLUS : CE QUI EST POSSIBLE ==={NC}
 1. Chargez 30 min minimum sur SECTEUR (pas USB PC), essayez un autre cable/chargeur.
 2. Forcer le redemarrage : Vol- + Power 10s (Samsung : Vol+ + Vol- + Power).
 3. Ca redemarre ? -> revenez au menu 1 ou 2.
 4. Ca vibre mais ecran noir ? -> le telephone FONCTIONNE : branchez-le,
    ce logiciel peut agir (menu 1/3), et une souris OTG remplace le tactile.
 5. Rien du tout ? -> panne materielle (batterie/connecteur/carte mere).
    Seule une reparation physique permet l'acces. Aucun logiciel ne peut
    'reveiller' un materiel mort : c'est une limite physique, pas de securite.

{RED}NOTE LEGALE : n'utilisez ces outils que sur vos propres appareils ou avec
l'autorisation explicite du propriétaire.{NC}
""")


def phone_to_phone_menu():
    title("Mode PHONE-A-PHONE (cet appareil = hôte, pas de PC)")
    if not IS_TERMUX:
        warn("Ce mode est conçu pour tourner SUR un téléphone via Termux.")
        print("""
INSTALLATION DE TERMUX SUR LE TELEPHONE HOTE :
  1. Installez Termux (F-Droid de preference : f-droid.org/fr/packages/com.termux)
  2. Dans Termux :
       pkg update && pkg install python android-tools
  3. Copiez ce script :  termux-setup-storage   (puis placez phonemedic.py
     dans le stockage) et lancez :  python phonemedic.py
  Le mode phone-a-phone apparaitra automatiquement au menu [7].
""")
        if input("Continuer quand même (PC/autre) ? [o/N] ").strip().lower() != "o":
            return
    while True:
        print(f"""
{CYAN}=== CONNECTION AU TELEPHONE CIBLE ==={NC}
 [1] Wi-Fi / Hotspot (SANS root, recommandé)
 [2] Câble USB + adaptateur OTG
 [3] Etat de la connexion actuelle
 [4] Déconnecter le téléphone cible
 [0] Retour""")
        c = input("Choix : ").strip()
        if c == "1":
            wifi_connect()
        elif c == "2":
            otg_connect()
        elif c == "3":
            _SERIAL_CACHE["v"] = None
            st = adb_state()
            devs = adb("devices")
            print(devs or "(vide)")
            log(f"Etat ADB : {st or 'aucune connexion'}")
        elif c == "4":
            tgt = input("Adresse ip:port a deconnecter : ").strip()
            if tgt:
                adb("disconnect", tgt)
                log("Deconnecte.")
        elif c == "0":
            return


def wifi_connect():
    print(f"""
{CYAN}PRINCIPE{NC} Les deux telephones partagent un reseau :
  - Le telephone HOTE active son point d'acces mobile (hotspot), OU les deux
    se connectent au meme Wi-Fi.
  - Sur le telephone CIBLE (celui qu'on controle) :
      Parametres > Options developpeur > 'Debogage sans fil' (Android 11+)
      -> 'Associer l'appareil avec un code d'appairage'
      -> notez : adresse IP:port d'appairage + code a 6 chiffres
      -> notez aussi l'IP:port affiche sous 'Adresse IP et port' (pour la connexion)
""")
    pair_addr = input("IP:PORT d'appairage (vide si deja appaire/Android<11) : ").strip()
    if pair_addr:
        code = input("Code d'appairage 6 chiffres : ").strip()
        out = run(["adb", "pair", pair_addr, code])
        print(out or "(pas de reponse)")
        if "success" in out.lower() or "ok" in out.lower():
            log("Appairage reussi !")
        else:
            err("Appairage echoue : verifiez IP, port et code affiches sur le telephone cible.")
            return
    conn_addr = input("IP:PORT de connexion (affiche sur le telephone cible) : ").strip()
    if not conn_addr:
        err("Adresse requise.")
        return
    adb("connect", conn_addr)
    time.sleep(1)
    _SERIAL_CACHE["v"] = None
    if adb_state() == "device":
        log("Telephone cible CONNECTE ! Tous les menus (1-6) agissent maintenant dessus.")
        diagnose()
    else:
        warn("Non connecte. Verifications :")
        print("  - Les deux telephones sont-ils sur le MEME reseau ?")
        print("  - 'Debogage sans fil' reste-t-il actif sur le cible ?")
        print("  - Certains hotspots isolent les clients : desactivez 'isolation' ou testez en Wi-Fi partage.")


def otg_connect():
    print(f"""
{CYAN}MATERIEL{NC}
  Telephone HOTE (celui-ci) --adaptateur OTG--> cable USB --> Telephone CIBLE.
  Adaptateurs : USB-C OTG femelle, ou Micro-USB OTG selon l'hote.

{CYAN}SUR LE TELEPHONE CIBLE{NC}
  Debogage USB ACTIVE + autorisation accordee (ecran fonctionnel ou souris OTG).
  Pour fastboot : redemarrez le cible en bootloader AVANT de brancher.
""")
    if not IS_TERMUX and os.geteuid() != 0:
        warn("Hors Termux/root, l'acces USB brut peut echouer.")
    log("Detection...")
    devs_out = run(["adb", "devices"])
    print(devs_out or "(adb ne repond pas)")
    fb_out = run(["fastboot", "devices"])
    if fb_out:
        print(fb_out)
        log("Telephone cible detecte en mode FASTBOOT.")
    low = (devs_out + fb_out).lower()
    if "no permissions" in low or "insufficient permissions" in low:
        err("Acces USB refuse par Android (cas classique SANS root).")
        print("""
SOLUTIONS DANS L'ORDRE :
 1. PREFERE : utilisez le mode Wi-Fi/hotspot (menu precedent) -> marche sans root.
 2. Si le telephone HOTE est ROOTE (Magisk/SuperSU) : accordez l'accès USB a
    Termux ; adb/fastboot fonctionneront alors completement par câble.
 3. Branche/rebranche l'adaptateur OTG apres avoir lance Termux.""")
    elif "\tdevice" in devs_out or fb_out:
        log("Connexion OK ! Menus 1-6 utilisables directement.")
        _SERIAL_CACHE["v"] = None
    else:
        warn("Rien detecte : verifiez adaptateur OTG, cable DATA (pas charge seul), et debogage USB du cible.")


def main_menu():
    while True:
        print(f"""
{CYAN}==================================================={NC}
   PHONE-MEDIC - Diagnostic / DevMode / Recuperation / SIM
{CYAN}==================================================={NC}
 [1] Diagnostic de l'appareil connecte
 [2] Assistant Mode developpeur + Debogage USB
 [3] Recuperation semi-brique (fastboot / firmware)
 [4] Carte SIM : verrouillage operateur, deblocage, eSIM
 [5] Telephone eteint / mort : options reelles
 [6] PHONE-A-PHONE : controler un telephone depuis un autre (Termux)
 [0] Quitter""")
        c = input("Choix : ").strip()
        if c == "1":
            diagnose()
        elif c == "2":
            guide_devmode()
        elif c == "3":
            recovery_menu()
        elif c == "4":
            sim_menu()
        elif c == "5":
            dead_phone_info()
        elif c == "6":
            phone_to_phone_menu()
        elif c == "0":
            sys.exit(0)


if __name__ == "__main__":
    if os.name == "nt":
        os.system("")
    print(f"{GREEN}Phone-Medic v1.0 — multiplateforme (Windows/macOS/Linux/Termux){NC}")
    if check_tools():
        main_menu()
