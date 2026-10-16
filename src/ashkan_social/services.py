# Application services: validated social actions and parameterized persistence.
from dataclasses import dataclass


@dataclass(frozen=True)
class FeedFilter:
    keyword: str = ""
    bookmarked_only: bool = False
    following_only: bool = False


class SocialService:
    def __init__(self, store):
        self.store = store

    def feed(self, user_id, filters=None, limit=100):
        filters = filters or FeedFilter()
        clauses = []
        params = [user_id, user_id]
        if filters.keyword.strip():
            clauses.append('(p.body LIKE ? OR u.username LIKE ? OR u.display_name LIKE ?)')
            term = '%' + filters.keyword.strip()[:100].replace('%', r'\%').replace('_', r'\_') + '%'
            params += [term, term, term]
        if filters.bookmarked_only:
            clauses.append('EXISTS(SELECT 1 FROM bookmarks b WHERE b.post_id=p.id AND b.user_id=?)')
            params.append(user_id)
        if filters.following_only:
            clauses.append('(p.user_id=? OR EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=? AND f.following_id=p.user_id))')
            params += [user_id, user_id]
        where = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
        params.append(min(max(int(limit), 1), 200))
        return self.store.query(f"""SELECT p.id,p.user_id,u.username,u.display_name,p.body,p.created_at,
          (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) AS likes,
          (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id) AS comments,
          EXISTS(SELECT 1 FROM bookmarks b WHERE b.post_id=p.id AND b.user_id=?) AS bookmarked,
          EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=?) AS liked
          FROM posts p JOIN users u ON u.id=p.user_id {where} ORDER BY p.id DESC LIMIT ?""", tuple(params))

    def toggle_bookmark(self, user_id, post_id):
        if self.store.query('SELECT 1 FROM bookmarks WHERE user_id=? AND post_id=?',(user_id,post_id)):
            self.store.execute('DELETE FROM bookmarks WHERE user_id=? AND post_id=?',(user_id,post_id))
            return False
        self.store.execute('INSERT INTO bookmarks(user_id,post_id) VALUES(?,?)',(user_id,post_id))
        return True

    def delete_own_post(self, user_id, post_id):
        cursor=self.store.execute('DELETE FROM posts WHERE id=? AND user_id=?',(post_id,user_id))
        return cursor.rowcount == 1

    def report_post(self, user_id, post_id, reason):
        reason=reason.strip()
        if not 5 <= len(reason) <= 500:
            raise ValueError('Report reason must be 5–500 characters.')
        post=self.store.query('SELECT user_id FROM posts WHERE id=?',(post_id,))
        if not post or post[0]['user_id']==user_id:
            raise ValueError('You can only report another member’s existing post.')
        self.store.execute('INSERT INTO reports(reporter_id,post_id,reason) VALUES(?,?,?)',(user_id,post_id,reason))

    def search_members(self, user_id, keyword=''):
        term='%' + keyword.strip()[:100].replace('%',r'\%').replace('_',r'\_') + '%'
        return self.store.query("""SELECT id,username,display_name,bio FROM users
          WHERE id!=? AND (username LIKE ? OR display_name LIKE ?) ORDER BY username LIMIT 100""",(user_id,term,term))

    def stats(self, user_id):
        return {
          'posts': self.store.query('SELECT COUNT(*) n FROM posts WHERE user_id=?',(user_id,))[0]['n'],
          'followers': self.store.query('SELECT COUNT(*) n FROM follows WHERE following_id=?',(user_id,))[0]['n'],
          'following': self.store.query('SELECT COUNT(*) n FROM follows WHERE follower_id=?',(user_id,))[0]['n'],
          'saved': self.store.query('SELECT COUNT(*) n FROM bookmarks WHERE user_id=?',(user_id,))[0]['n'],
        }
