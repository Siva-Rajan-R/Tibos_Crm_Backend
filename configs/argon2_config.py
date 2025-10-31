from argon2 import PasswordHasher
from argon2.exceptions import VerificationError,VerifyMismatchError

hasher=PasswordHasher()