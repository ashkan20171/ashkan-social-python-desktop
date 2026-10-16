import tempfile
import unittest
from pathlib import Path
from ashkan_social.db import Store
from ashkan_social.auth import register

class V3Tests(unittest.TestCase):
    def test_draft_and_block_tables(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d)/'db.sqlite')
            a=register(store,'alice','Alice','strong-password-123')
            b=register(store,'bob','Bob','strong-password-456')
            users=store.query('SELECT id FROM users ORDER BY id')
            aid,bid=[r['id'] for r in users]
            store.execute('INSERT INTO drafts(user_id,body) VALUES(?,?)',(aid,'Hello draft'))
            store.execute('INSERT INTO blocks(blocker_id,blocked_id) VALUES(?,?)',(aid,bid))
            self.assertEqual(store.query('SELECT body FROM drafts')[0]['body'],'Hello draft')
            self.assertEqual(len(store.query('SELECT * FROM blocks')),1)
            store.close()
