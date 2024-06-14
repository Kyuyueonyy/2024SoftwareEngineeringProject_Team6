import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:rlarbdus3470!@127.0.0.1/swdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
