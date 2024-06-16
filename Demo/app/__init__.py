import os 
import sqlalchemy
from yaml import load, Loader
from flask import Flask

import pymysql 
from sqlalchemy import text 




def init_connection_engine():
    # detect env local or gcp
    if os.environ.get('GAE_ENV') != 'standard':
        try:
            variables = load(open("app.yaml"), Loader=Loader)
        except OSError as e:
            print("Make sure you have the app.yaml file setup")
            os.exit()

        env_variables = variables['env_variables']
        for var in env_variables:
            os.environ[var] = env_variables[var]

    # pool = sqlalchemy.create_engine(
    #         sqlalchemy.engine.url.URL(
    #             drivername="mysql+pymysql",
    #             username=os.environ.get('MYSQL_USER'),
    #             password=os.environ.get('MYSQL_PASSWORD'),
    #             database=os.environ.get('MYSQL_DB'),
    #             host=os.environ.get('MYSQL_HOST'),
    #             port = os.environ.get('MYSQL_PORT'),
    #             query = os.environ.get('MYSQL_QUERY')

    #         )
    #     )
    # return pool

    # make sure to add a network 
    connect_string = f'mysql+pymysql://root:cs411@35.225.178.245/proj'
    pool = sqlalchemy.create_engine(connect_string)
    return pool



app = Flask(__name__)

db = init_connection_engine()

with db.connect() as conn:
    query = "Select * from airlines limit 15"
    results = conn.execute(text(query))
    print([x for x in results])


from app import routes
