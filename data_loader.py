import logging
import pickle

import pandas as pd


def load_pickle_file(path):
    try:
        with open(path, 'rb') as p:
            return pickle.load(p)
    except Exception as e:
        logging.error(f"Error loading {path}. {str(e)}")
        return None


def load_csv_file(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        logging.error(f"Error loading {path}. {str(e)}")
        return None