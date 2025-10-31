from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os
load_dotenv()

symme=Fernet(key=os.getenv("SYMME_KEY"))