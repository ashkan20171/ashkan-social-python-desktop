import tempfile
import unittest
from pathlib import Path
from src.ashkan_social.db import Store
from src.ashkan_social.auth import register
from src.ashkan_social.services import SocialService, FeedFilter


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Store(Path(self.tmp.name)/'test.db')
        self.alice=register(self.db,'alice','Alice','password123')
        self.bob=register(self.db,'bob','Bob','password123')
        self.service=SocialService(self.db)
        self.post=self.db.execute('INSERT INTO posts(user_id,body) VALUES(?,?)',(self.bob,'Hello world')).lastrowid

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_bookmark_and_feed(self):
        self.assertEqual(len(self.service.feed(self.alice,FeedFilter(bookmarked_only=True))),0)
        self.assertTrue(self.service.toggle_bookmark(self.alice,self.post))
        self.assertEqual(len(self.service.feed(self.alice,FeedFilter(bookmarked_only=True))),1)
        self.assertFalse(self.service.toggle_bookmark(self.alice,self.post))

    def test_delete_only_own(self):
        self.assertFalse(self.service.delete_own_post(self.alice,self.post))
        self.assertTrue(self.service.delete_own_post(self.bob,self.post))

    def test_following_feed(self):
        self.assertEqual(len(self.service.feed(self.alice,FeedFilter(following_only=True))),0)
        self.db.execute('INSERT INTO follows VALUES(?,?)',(self.alice,self.bob))
        self.assertEqual(len(self.service.feed(self.alice,FeedFilter(following_only=True))),1)

    def test_report_validation(self):
        with self.assertRaises(ValueError):
            self.service.report_post(self.bob,self.post,'spam spam')
        self.service.report_post(self.alice,self.post,'Unwanted advertising')
        self.assertEqual(len(self.db.query('SELECT * FROM reports')),1)

    def test_search(self):
        self.assertEqual(len(self.service.feed(self.alice,FeedFilter(keyword='world'))),1)
        self.assertEqual(len(self.service.feed(self.alice,FeedFilter(keyword='nomatch'))),0)
        self.assertEqual(len(self.service.search_members(self.alice,'bob')),1)

if __name__=='__main__': unittest.main()
