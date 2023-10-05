from mesh.database import MeshDB
from mesh.provisioning import Provisioner, Provisionee
db = MeshDB("database/example_database.json")
db.provisioners
p = Provisioner(device, db)
cc = ConfigurationClient(db)
device.model_add(cc)