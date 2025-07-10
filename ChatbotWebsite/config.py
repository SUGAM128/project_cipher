import os

class Config:
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or 'dev_secret_key'
    # SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or 'mysql+pymysql://root:@localhost/cipherdb'
#    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:mysecurepassword@localhost/cipherdb'
# SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/cipherdb'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/cipherdb'

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or 'pawpal950@gmail.com'
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or 'dvyjqulqnqgzrabi'
