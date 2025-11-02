import pyrebase
import os,json
from dotenv import load_dotenv
load_dotenv()

firebaseConfig = json.loads(os.getenv("FIREBASE_CONFIG"))
DEFAULT_SUPERADMIN_INFO=json.loads(os.getenv('DEFAULT_SUPERADMIN_INFO'))

fb=pyrebase.initialize_app(config=firebaseConfig)

fdb=fb.database()


