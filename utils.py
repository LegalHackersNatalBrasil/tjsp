from pymongo import MongoClient
from bson.json_util import dumps, loads
from datetime import datetime
import json


client = MongoClient()
to_db = client['LegalHackers']
to_collec = to_db['tjsp']


def restore_from_db(db_name, collection_name, insert_all=True, drop=False):
    from_db = client[db_name]
    from_collec = from_db[collection_name]

    all_process = from_collec.find()
    if drop:
        to_collec.drop()
    for process in all_process:
        find_process = to_collec.find_one(
            {'processo': process['processo'] }
        )
        if (not insert_all) and (not find_process):
            del process['_id']
            to_collec.insert_one(process)


def restore_from_json(file_name, db_name, collection_name, insert_all=True, drop=False):
    to_db = client[db_name]
    to_collec = to_db[collection_name]

    with open(f'{file_name}.json', 'r') as json_file:
        restored_process = loads(json_file.read())
    if drop:
        to_collec.drop()
    if insert_all:
        to_collec.insert_many(restored_process)
    else:
        for process in restored_process:
            find_process = to_collec.find_one(
                {'processo': process['processo']}
            )
            if not find_process:
                to_collec.insert_one(process)


def backup_db_json(db_name, collection_name):
    from_db = client[db_name]
    from_collec = from_db[collection_name]

    all_process = from_collec.find(projection={'_id': 0})
    json_process = dumps(all_process)
    with open(f'{db_name}_{collection_name}.json', 'w') as json_file:
        json_file.write(json_process)


def backup_db(db_name, collection_name):
    pass


if __name__ == '__main__':
    # restore_process_from('', '')
    # restore_from_json('', '', '')
    # to_json_file('', '')
    pass

