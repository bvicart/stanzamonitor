#!/usr/bin/python
# coding: utf8
##########################################################
# Utilité: Surveillance nouvelles stanza publiées par OCLC
# Auteur: Cyrille Haudebault
# Date de création: 17/04/2025
# Dernière modification: 17/04/2025
# Version: 3.0
#########################################################

import smtplib, os, logging, requests, re, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URL = 'https://help.oclc.org/Library_Management/EZproxy/EZproxy_database_stanzas/Database_stanzas/EZproxy_database_stanzas_-_All'
HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0'}
CURRENT_PATH = os.path.dirname(__file__)
CONFIG_FILE = "/usr/local/ezproxy/config.txt"
SMTP_SERVER = imaps.sorbonne-universite.fr
SMTP_PORT = 993
SENDER = edocadm@scd.upmc.fr
RECIPIENT = edocadm@scd.upmc.fr
STANZA_LST_FILE = os.path.join(CURRENT_PATH,'stanza_list.json')
LOG_FILE = os.path.join(CURRENT_PATH,"stanza_monitor.log")
stanza_dict = {}
stanza_lst = []
reg = r"\d{4}-\d{2}-\d{2}"

logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
        format="%(asctime)s - %(levelname)s - : %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
def mail(content:dict) -> None:
    """Création et envoi de mail

    Args:
        content (dict): Chaîne de caratère à inclure dans le mail
    """
    # Création d'un courriel
    message = MIMEMultipart("alternative")
    message["Subject"] = "🚨 _EZPROXY_ Nouvelle(s) version(s) de stanza"
    message["From"] = SENDER
    message["To"] = RECIPIENT
    text = ''
    for key, value in content.items():
        text += f"{key} : {value}\n"
    # Création d'un élément MIMEText 
    text_mime = MIMEText(text, 'plain', 'utf-8')
    # Ajout de l'élément dans le courriel
    message.attach(text_mime)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(SENDER, RECIPIENT, message.as_string())
        logging.info(f'Mail envoyé')
    except Exception as e:
        logging.error(f"Erreur d'envoi de mail : {e}")

def check_config(title:str) -> bool:
    """Vérification de l'utilisation des stanza

    Args:
        title (str): Titre de la stanza

    Returns:
        bool: True si utilisé dans le fichier de config
    """
    with open(CONFIG_FILE, 'r') as f:
        config = f.read()
        if title in config:
            return True
        else:
            return False

def write_json(data:dict):
    """Écris des données dans le fichier Json

    Args:
        data (dict): Données à écrire
    """
    with open(STANZA_LST_FILE,'w') as f:
        f.write(json.dumps(data,indent=4))

def check_date(title:str, date:str) -> bool:
    d={"title":title,"date":date}
    if os.path.isfile(STANZA_LST_FILE):
        with open(STANZA_LST_FILE, 'r') as f:
            stanza_lst = json.load(f)
    else:
        write_json({"stanza":[]})
    found = False
    for stanza in stanza_lst['stanza']:
        if title == stanza['title']:
            found = True
            if date != stanza['date']:
                index = stanza_lst['stanza'].index(stanza)
                logging.warning('Stanza à mettre à jour')
                up_to_date = False
            else:
                up_to_date = True
        else:
            pass
    if not found:
        stanza_lst['stanza'].append(d)
        write_json(stanza_lst)
        up_to_date = True
    if not up_to_date:
        stanza_lst['stanza'].pop(index)
        stanza_lst['stanza'].insert(index,d)
        write_json(stanza_lst)
    return up_to_date


def webscrap():
    """ Scrap et comparaison """
    logging.info("Vérification du site OCLC")
    try:
        page = requests.get(URL, headers=HEADER, verify=True)
        lines = str(page.content).split('</p>')[4].split('</li>')
        logging.info('Site récupéré et conforme')
        for line in lines:
            try:
                title = line.split('</a>')[0].split('>')[-1]
                date = re.search(reg,line).group()
                link = line.split('href="')[1].split('"')[0]
                used = check_config(title)
                if used:
                    up_to_date = check_date(title, date)
                    if not up_to_date:
                        stanza_dict[title] = link
                        logging.info(f'{title} : {link}')
                else:
                    pass
            except:
                pass
                
        if stanza_dict:
            mail(stanza_dict)
        else:
            logging.info('Aucune nouvelle stanza')
        
    except Exception as e:
        logging.error(f"Problème de récupération du site OCLC : {e}")

logging.info('Début du script')
webscrap()
logging.info('Fin du script')

