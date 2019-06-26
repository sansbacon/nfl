'''

db.py

setup automap classes

'''
import logging
import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Insert


logger = logging.getLogger(__name__)


@compiles(Insert)
def prefix_inserts(insert, compiler, **kw):
    """
    Adds "ON CONFLICT DO NOTHING" to inserts

    Args:
        insert:
        compiler:
        **kw:

    Returns:

    """
    # ON CONFLICT clause comes before RETURN clause
    # https://stackoverflow.com/questions/33307250/
    # postgresql-on-conflict-in-sqlalchemy
    s = compiler.visit_insert(insert, **kw)
    if ' RETURNING ' in s:
        return s.replace(' RETURNING ', ' ON CONFLICT DO NOTHING RETURNING ')
    return s + ' ON CONFLICT DO NOTHING'


def setup(database='sqlite',
               database_file='../data/nfl.sqlite', 
               schema=None):
    '''
    Automaps classes
    
    Args:
        database(str): default 'sqlite'
        database_file(str): default '../nfl.sqlite'
        schema(str): default None
        
    Returns:
        Base, engine, session

    '''
    if database in ['postgresql', 'postgres', 'pg']:
        db_user = os.getenv('NFL_PG_USER')
        db_pwd = os.getenv('NFL_PG_PWD')
        db_host = os.getenv('NFL_PG_HOST')
        db_port = os.getenv('NFL_PG_PORT')
        db_db = os.getenv('NFL_PG_DB')

        connstr = (
            f"postgresql://{db_user}:{db_pwd}@{db_host}"
            f":{db_port}/{db_db}"
        )
    
    elif database == 'sqlite':
        connstr = f'sqlite:///{database_file}'

    eng = create_engine(connstr)
    session = Session(eng)

    # create metadata
    metadata = MetaData()
    metadata.reflect(eng)

    # create classes
    Base = automap_base(metadata=metadata)
    if schema:
        Base.metadata.reflect(bind=eng, schema=schema)
    else:
        Base.metadata.reflect(bind=eng)
    Base.prepare(eng)

    return Base, eng, session


def execproc(procname, engine, queryParams=[]):
    """
    Executes postgresql stored procedure

    Args:
        procname(str): name of the stored procedure
        engine(engine): sqlalchemy engine
        queryParams(list): in parameters for stored procedure

    Returns:
        list: of dict

    Usage:
        pivot = execproc('drbb.fn_player_scoring_pivot', eng)

    """
    connection = engine.raw_connection()
    cursor = connection.cursor()
    try:
        cursor.callproc(procname, queryParams)
        cols = [col.name for col in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        cursor.close()
        connection.commit()
        return rows
    finally:
        connection.close()
