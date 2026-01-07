from cryptography.fernet import Fernet
import os
from ...settings import SETTINGS

symme=Fernet(key=SETTINGS.SYMME_KEY)