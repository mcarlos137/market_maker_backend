from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.bot_db import BotDB

DBS: dict = {
    'exchange': {},
    'bot': {}
}

def get_exchange_db(db_connection: str) -> ExchangeDB:
    if db_connection not in DBS['exchange']:
        DBS['exchange'][db_connection] = ExchangeDB(db_connection=db_connection)
    return DBS['exchange'][db_connection]

def get_bot_db(db_connection: str, bot_type: str) -> BotDB:
    if db_connection not in DBS['bot']:
        DBS['bot'][db_connection] = BotDB(db_connection=db_connection, bot_type=bot_type)
    return DBS['bot'][db_connection]
