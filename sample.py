import json
import pymongo
client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
db = client.get_database('total_records')


# parse and add the json content to db
if __name__ == '__main__':
    f = open("./Mesh_demo.json")
    data = json.load(f)
    for chip in data:
        db.chip_info.insert_one(chip)