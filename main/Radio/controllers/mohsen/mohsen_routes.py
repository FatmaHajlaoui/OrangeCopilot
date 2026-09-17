from datetime import datetime

import pandas as pd
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from dateutil.parser import *
from openpyxl import load_workbook

from main.Radio.controllers.api.radio_api_utils import optim_radio
from main.Radio.services.mohsen_service import MohsenService
from main.utils.logging_config import configure_logging
from main.utils.utils import role_required

radio_mohsen_bp = Blueprint(
    'radio_mohsen_bp', __name__,
    static_folder='static',
    template_folder='templates'
)

ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@radio_mohsen_bp.route('/mohsen')
@login_required
@role_required(['USER_FH_RADIO', 'ADMIN', 'USER_FH'])
def mohsen_page():
    df = MohsenService.get_files_list()
    return render_template("Radio/mohsen/mohsen.html", df_mohsen=df)


@radio_mohsen_bp.route("/mohsen/delete", methods=['GET', 'POST'])
def delete_mohsen_file():
    if request.method == 'POST':
        creation_date = pd.to_datetime(parse(request.form['creation_date'], fuzzy=True).strftime("%d-%m-%Y %H:%M:%S"))
        MohsenService.remove_file(creation_date)

        logger = configure_logging()
        logger.info(f"Fichier Optim_Radio du {creation_date} supprime par {current_user.username}")

    return jsonify({'status': 'success',
                    'message': 'Fichier supprimé avec success !'})


@radio_mohsen_bp.route("/mohsen/upload_file", methods=["GET", "POST"])
def upload_new_file():
    logger = configure_logging()  # Initialisation du logger

    try:
        files = request.files.getlist('battery_file[]')
        df1, df2 = None, None

        if not files:
            return jsonify({'status': 'error', 'message': 'Aucun fichier téléchargé.'})

        for file in files:
            try:
                data = pd.read_csv(file, skiprows=6)
            except pd.errors.EmptyDataError:
                return jsonify({'status': 'error', 'message': "Le fichier est vide ou corrompu."})
            except pd.errors.ParserError:
                return jsonify({'status': 'error', 'message': "Erreur de format du fichier. Assurez-vous qu'il s'agit d'un fichier CSV valide."})
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier CSV : {str(e)}")
                return jsonify({'status': 'error', 'message': "Une erreur inattendue s'est produite lors de la lecture du fichier."})

            # Vérification des colonnes pour assigner à df1 ou df2
            if data.columns.tolist() == ['Time', 'RNC', 'NodeB Name', 'Cell Name', 'Cell ID', 'Integrity', 'VS.MeanRTWP(dBm)']:
                df1 = data
            else:
                df2 = data

        # S'assurer que df1 et df2 ont bien été assignés
        if df1 is None:
            return jsonify({'status': 'error', 'message': "Le fichier ne contient pas les colonnes attendues pour df1."})
        if df2 is None:
            return jsonify({'status': 'error', 'message': "Le fichier ne contient pas les colonnes attendues pour df2."})

        # Optimisation des données et ajout de la date de création
        try:
            df = optim_radio(df2, df1)
        except KeyError as e:
            logger.error(f"Clé manquante lors de l'optimisation des données : {str(e)}")
            return jsonify({'status': 'error', 'message': "Une clé attendue est manquante dans les fichiers. Vérifiez les colonnes."})
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation des fichiers : {str(e)}")
            return jsonify({'status': 'error', 'message': "Une erreur s'est produite lors de l'optimisation des données."})

        try:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            df["Creation Date"] = formatted_datetime
            df["Creation Date"] = pd.to_datetime(df["Creation Date"])

            MohsenService.add_new_file(df)
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du fichier dans MohsenService : {str(e)}")
            return jsonify({'status': 'error', 'message': "Une erreur s'est produite lors de l'ajout du fichier dans la base de données."})

        # Journalisation de l'ajout réussi
        logger.info(f"Nouveau Fichier Battery ajouté par {current_user.username}")

        return jsonify({'status': 'success', 'message': 'Fichier ajouté avec succès !'})

    except Exception as e:
        logger.error(f"Erreur inattendue : {str(e)}")
        return jsonify({'status': 'error', 'message': "Une erreur inattendue s'est produite. Veuillez réessayer."})



