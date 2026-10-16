import tempfile
import unittest
from pathlib import Path
from src.ashkan_social.db import Store
from src.ashkan_social.auth import register, login

class AuthTests(unittest.TestCase):
    def test_registration_and_login(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'test.db')
            register(store,'test_user','Test User','strongpassword')
            self.assertIsNotNone(login(store,'test_user','strongpassword'))
            self.assertIsNone(login(store,'test_user','wrongpassword'))

if __name__=='__main__':unittest.main()
