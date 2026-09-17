import numpy as np
import pandas as pd
from sqlalchemy import func, desc

from main import db, get_redis_instance
from main.Radio.models.models import Mohsen
from main.utils.redis_utils import write_df_to_redis, redis_delete_df

pd.options.mode.chained_assignment = None


class MohsenService:

    @staticmethod
    def add_new_file(df):
        try:
            new_names = [
                'Cell_Name',
                'mean_rtwp',
                'max_rtwp',
                'min_rtwp',
                'occ_rtwp_gt_98' ,
                'vs_mean_rtwp_ant0' ,
                'vs_mean_rtwp_ant1',
                'occ_diff_sect_gt_5',
                'creation_date'
            ]

            # use rename to replace column names
            df.rename(columns=dict(zip(df.columns, new_names)), inplace=True)
            df = df.replace({np.nan: None})

            # convert the dataframe to a list of dictionaries
            records = df.to_dict(orient='records')

            # insert the data into the database using bulk_insert_mappings
            db.session.bulk_insert_mappings(Mohsen, records)
            db.session.commit()
            return True
        except (Exception,):
            raise Exception("Impossible d'ajouter le fichier; veuillez verifier les colonnes fournies !")

    @staticmethod
    def get_data(creation_date=None):
        last_date = creation_date or db.session.query(func.max(Mohsen.creation_date)).scalar()
        # unix_timestamp = int(datetime.timestamp(last_date))

        if not last_date:
            return None

        redis_instance = get_redis_instance()
        redis_key = f'radio_mohsen_{pd.to_datetime(last_date).strftime("%d-%m-%Y %H:%M:%S")}'

        # Check if data exists in Redis cache
        cached_data = redis_instance.get(redis_key)
        if cached_data:
            return pd.read_json(cached_data.decode('utf-8'))

        # Data not found in Redis cache, query from database
        data = db.session.query(
            Mohsen.Cell_Name,
            Mohsen.mean_rtwp,
            Mohsen.max_rtwp,
            Mohsen.min_rtwp,
            Mohsen.occ_rtwp_gt_98,
            Mohsen.vs_mean_rtwp_ant0,
            Mohsen.vs_mean_rtwp_ant1,
            Mohsen.occ_diff_sect_gt_5,


        ).filter(Mohsen.creation_date == last_date)

        df = pd.DataFrame(
            [
                (
                    d.Cell_Name,
                    d.mean_rtwp,
                    d.max_rtwp,
                    d.min_rtwp,
                    d.occ_rtwp_gt_98,
                    d.vs_mean_rtwp_ant0,
                    d.vs_mean_rtwp_ant1,
                    d.occ_diff_sect_gt_5,
                )
                for d in data
            ],
            columns=[
            'Cell_Name',
            'mean_rtwp',
            'max_rtwp',
            'min_rtwp',
            'occ_rtwp_gt_98',
            'vs_mean_rtwp_ant0',
            'vs_mean_rtwp_ant1',
            'occ_diff_sect_gt_5',

            ],
        )

        # Cache data in Redis
        write_df_to_redis(df, redis_key)


        return df

    @staticmethod
    def get_files_list():
        data = db.session.query(Mohsen.creation_date.distinct()). \
            order_by(desc(Mohsen.creation_date)).all()
        df = pd.DataFrame([d for d in data], columns=['CreationDate'])
        return df

    @staticmethod
    def remove_file(creation_date):
        battery_obj = MohsenService.get_data_by_upload_date(creation_date)
        if battery_obj:
            delete_records = Mohsen.__table__.delete().where(Mohsen.creation_date == creation_date)
            db.session.execute(delete_records)
            db.session.commit()
            redis_key = f'radio_mohsen_{pd.to_datetime(creation_date).strftime("%d-%m-%Y %H:%M:%S")}'
            redis_delete_df(redis_key)
            return True
        else:
            raise Exception("Le fichier n'existe pas")

    @staticmethod
    def get_data_by_upload_date(upload_date):
        battery_obj = Mohsen.query.filter_by(
            creation_date=upload_date,
        ).first()
        return battery_obj
