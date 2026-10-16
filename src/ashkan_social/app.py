import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QListWidget, QMessageBox, QStackedWidget, QInputDialog)
from .db import Store
from .auth import login, register
from .services import SocialService, FeedFilter

LIGHT_STYLE = """
QWidget {background:#F5F7FC;color:#17243A;font-family:Segoe UI;font-size:13px}
QLineEdit,QTextEdit,QListWidget {background:#FFFFFF;border:1px solid #D8E1F0;border-radius:12px;padding:11px;selection-background-color:#A5B4FC}
QPushButton {background:#4F46E5;color:white;border:0;border-radius:11px;padding:11px 17px;font-weight:600}
QPushButton:hover {background:#6366F1}
QLabel#heading {font-size:25px;font-weight:700;color:#1E293B}
QLabel#muted {color:#64748B}
QPushButton#secondary {background:#E8EDFA;color:#334155;border:1px solid #CDD7EC}
QPushButton#danger {background:#B91C1C;color:white}
QListWidget::item {padding:13px;border-bottom:1px solid #E2E8F0}
QListWidget::item:selected {background:#DDE6FA;border-radius:8px}
"""
STYLE = '''
QWidget {background:#0B1220;color:#E7EDF8;font-family:Segoe UI;font-size:13px}
QLineEdit,QTextEdit,QListWidget {background:#17243A;border:1px solid #30435E;border-radius:12px;padding:11px;selection-background-color:#6366F1}
QPushButton {background:#4F46E5;border:0;border-radius:11px;padding:11px 17px;font-weight:600}
QPushButton:hover {background:#6366F1}
QPushButton:pressed {background:#3730A3}
QLabel#heading {font-size:25px;font-weight:700;color:#F8FAFC}
QLabel#muted {color:#9CAEC8}
QPushButton#secondary {background:#1F304B;color:#CBD5E1;border:1px solid #354766}
QPushButton#secondary:hover {background:#304766}
QPushButton#danger {background:#933C4B}
QListWidget::item {padding:13px;border-bottom:1px solid #30435E}
QListWidget::item:selected {background:#263D64;border-radius:8px}
QLineEdit:focus,QTextEdit:focus,QListWidget:focus {border:1px solid #818CF8}

'''

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.store = Store()
        self.social = SocialService(self.store)
        self.feed_mode = "all"
        self.light_theme = False
        self.user = None
        self.setWindowTitle('Ashkan Social • Community Studio')
        self.resize(1120, 750)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.auth_screen()

    def page(self, title):
        root = QWidget(); layout = QVBoxLayout(root); layout.setContentsMargins(35,25,35,25); layout.setSpacing(15)
        heading = QLabel(title); heading.setObjectName('heading'); layout.addWidget(heading)
        return root, layout

    def auth_screen(self):
        root, layout = self.page('✦  ASHKAN SOCIAL')
        layout.addWidget(QLabel('A modern community space · Sign in or create an account'))
        self.username = QLineEdit(); self.username.setPlaceholderText('Username')
        self.name = QLineEdit(); self.name.setPlaceholderText('Display name (registration)')
        self.password = QLineEdit(); self.password.setPlaceholderText('Password'); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        for w in (self.username,self.name,self.password): layout.addWidget(w)
        for title, handler in [('Sign in', self.signin), ('Create account', self.signup)]:
            b = QPushButton(title); b.clicked.connect(handler); layout.addWidget(b)
        layout.addStretch(); self.stack.addWidget(root); self.stack.setCurrentWidget(root)

    def signin(self):
        self.user = login(self.store,self.username.text(),self.password.text())
        if self.user: self.home()
        else: QMessageBox.warning(self,'Sign in','Invalid username or password.')

    def signup(self):
        try:
            register(self.store,self.username.text(),self.name.text(),self.password.text())
            self.signin()
        except Exception as exc:
            QMessageBox.warning(self,'Registration',str(exc))

    def home(self):
        root, layout = self.page('✦  ASHKAN SOCIAL  /  Discover & Connect')
        bar = QHBoxLayout()
        for label, action in [('Feed',self.show_feed),('Saved',self.saved_posts),('Following',self.following_feed),('Explore',self.explore),('Messages',self.messages),('Notifications',self.notifications),('Profile',self.profile),('Drafts',self.drafts),('Theme',self.toggle_theme),('Log out',self.logout)]:
            button=QPushButton(label); button.clicked.connect(action); bar.addWidget(button)
        layout.addLayout(bar)
        self.content = QVBoxLayout(); layout.addLayout(self.content)
        self.stack.addWidget(root); self.stack.setCurrentWidget(root)
        self.feed_mode='all'
        self.show_feed()

    def clear_content(self):
        while self.content.count():
            item=self.content.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child=item.layout().takeAt(0)
                    if child.widget(): child.widget().deleteLater()

    def label(self,text):
        w=QLabel(text); w.setWordWrap(True); self.content.addWidget(w)

    def saved_posts(self):
        self.feed_mode = 'saved'
        self.show_feed()

    def following_feed(self):
        self.feed_mode = 'following'
        self.show_feed()

    def show_feed(self):
        self.clear_content()
        mode = self.feed_mode
        self.label({'all':'Community feed','saved':'Your saved posts','following':'People you follow'}[mode])
        self.search_posts = QLineEdit()
        self.search_posts.setPlaceholderText('Search posts or authors…')
        self.search_posts.returnPressed.connect(self.refresh_posts)
        self.content.addWidget(self.search_posts)
        search_button = QPushButton('Search')
        search_button.clicked.connect(self.refresh_posts)
        self.content.addWidget(search_button)
        if mode == 'all':
            self.composer=QTextEdit()
            self.composer.setPlaceholderText('Share an update with your community…')
            self.composer.setMaximumHeight(95)
            self.content.addWidget(self.composer)
            b=QPushButton('Publish post')
            b.clicked.connect(self.publish)
            self.content.addWidget(b)
        self.items=QListWidget()
        self.content.addWidget(self.items)
        self.refresh_posts()
        actions=QHBoxLayout()
        for name,handler in [('♥ Like',self.like),('Comment',self.comment),('Comments',self.view_comments),('☆ Save',self.bookmark),('Report',self.report),('Edit mine',self.edit_post),('Delete mine',self.delete_post)]:
            btn=QPushButton(name)
            btn.setObjectName('secondary' if name!='Delete mine' else 'danger')
            btn.clicked.connect(handler)
            actions.addWidget(btn)
        self.content.addLayout(actions)
        if mode == 'all':
            draft_btn=QPushButton('Save composer as draft'); draft_btn.setObjectName('secondary'); draft_btn.clicked.connect(self.save_draft); self.content.addWidget(draft_btn)

    def refresh_posts(self):
        selected = self.selected_post() if hasattr(self,'post_ids') else None
        filters=FeedFilter(keyword=self.search_posts.text(),bookmarked_only=self.feed_mode=='saved',following_only=self.feed_mode=='following')
        rows=self.social.feed(self.user['id'],filters)
        self.post_ids=[r['id'] for r in rows]
        self.items.clear()
        for r in rows:
            badge='★ ' if r['bookmarked'] else ''
            heart='♥' if r['liked'] else '♡'
            self.items.addItem(f"{badge}{r['display_name']}  @{r['username']}  ·  {r['created_at']}\n{r['body']}\n{heart} {r['likes']}   ◇ {r['comments']} comments")
        if selected in self.post_ids:
            self.items.setCurrentRow(self.post_ids.index(selected))

    def bookmark(self):
        post=self.selected_post()
        if post is not None:
            self.social.toggle_bookmark(self.user['id'],post)
            self.refresh_posts()

    def delete_post(self):
        post=self.selected_post()
        if post is None:return
        if QMessageBox.question(self,'Delete post','Delete your selected post permanently?') != QMessageBox.StandardButton.Yes:return
        if not self.social.delete_own_post(self.user['id'],post):
            QMessageBox.warning(self,'Delete post','Only your own posts can be deleted.')
        self.refresh_posts()

    def report(self):
        post=self.selected_post()
        if post is None:return
        reason,ok=QInputDialog.getMultiLineText(self,'Report post','Why are you reporting this post?')
        if ok:
            try:
                self.social.report_post(self.user['id'],post,reason)
                QMessageBox.information(self,'Report','Report saved for review.')
            except ValueError as exc:
                QMessageBox.warning(self,'Report',str(exc))

    def edit_post(self):
        post=self.selected_post()
        if post is None:return
        rows=self.store.query('SELECT body FROM posts WHERE id=? AND user_id=?',(post,self.user['id']))
        if not rows:return QMessageBox.warning(self,'Edit','You can edit only your own posts.')
        body,ok=QInputDialog.getMultiLineText(self,'Edit post','Update your post:',rows[0]['body'])
        if ok:
            body=body.strip()
            if not 1<=len(body)<=2000:return QMessageBox.warning(self,'Edit','Post must contain 1–2000 characters.')
            self.store.execute('UPDATE posts SET body=? WHERE id=? AND user_id=?',(body,post,self.user['id']))
            self.refresh_posts()

    def save_draft(self):
        body=self.composer.toPlainText().strip()
        if not 1<=len(body)<=2000:return QMessageBox.warning(self,'Draft','Draft must contain 1–2000 characters.')
        self.store.execute('INSERT INTO drafts(user_id,body) VALUES(?,?)',(self.user['id'],body))
        self.composer.clear()
        QMessageBox.information(self,'Draft','Draft saved locally.')

    def drafts(self):
        self.clear_content(); self.label('Your drafts · private and saved on this device')
        rows=self.store.query('SELECT id,body,updated_at FROM drafts WHERE user_id=? ORDER BY id DESC',(self.user['id'],))
        self.draft_ids=[r['id'] for r in rows]
        self.draft_items=QListWidget(); self.content.addWidget(self.draft_items)
        for r in rows:self.draft_items.addItem(f"{r['updated_at']}\n{r['body']}")
        for title,fn in [('Publish selected draft',self.publish_draft),('Delete selected draft',self.delete_draft)]:
            b=QPushButton(title); b.clicked.connect(fn); self.content.addWidget(b)

    def selected_draft(self):
        idx=self.draft_items.currentRow()
        return self.draft_ids[idx] if 0<=idx<len(self.draft_ids) else None

    def publish_draft(self):
        did=self.selected_draft()
        if did is None:return
        rows=self.store.query('SELECT body FROM drafts WHERE id=? AND user_id=?',(did,self.user['id']))
        if not rows:return
        with self.store.conn:
            self.store.conn.execute('INSERT INTO posts(user_id,body) VALUES(?,?)',(self.user['id'],rows[0]['body']))
            self.store.conn.execute('DELETE FROM drafts WHERE id=? AND user_id=?',(did,self.user['id']))
        self.feed_mode='all';self.show_feed()

    def delete_draft(self):
        did=self.selected_draft()
        if did is None:return
        self.store.execute('DELETE FROM drafts WHERE id=? AND user_id=?',(did,self.user['id']))
        self.drafts()

    def toggle_theme(self):
        self.light_theme=not self.light_theme
        QApplication.instance().setStyleSheet(LIGHT_STYLE if self.light_theme else STYLE)

    def selected_post(self):
        index=self.items.currentRow()
        return self.post_ids[index] if 0 <= index < len(self.post_ids) else None

    def publish(self):
        body=self.composer.toPlainText().strip()
        if not body or len(body)>2000: return QMessageBox.warning(self,'Post','Enter 1–2000 characters.')
        self.store.execute('INSERT INTO posts(user_id,body) VALUES(?,?)',(self.user['id'],body)); self.show_feed()

    def like(self):
        post=self.selected_post()
        if post is None: return
        if self.store.query('SELECT 1 FROM likes WHERE user_id=? AND post_id=?',(self.user['id'],post)):
            self.store.execute('DELETE FROM likes WHERE user_id=? AND post_id=?',(self.user['id'],post))
        else: self.store.execute('INSERT INTO likes VALUES(?,?)',(self.user['id'],post))
        self.refresh_posts()

    def comment(self):
        post=self.selected_post()
        if post is None: return
        body,ok=QInputDialog.getMultiLineText(self,'Comment','Your comment:')
        if ok and body.strip() and len(body)<=1000:
            self.store.execute('INSERT INTO comments(post_id,user_id,body) VALUES(?,?,?)',(post,self.user['id'],body.strip()))
            self.refresh_posts()

    def view_comments(self):
        post=self.selected_post()
        if post is None: return
        rows=self.store.query('SELECT u.display_name,c.body FROM comments c JOIN users u ON u.id=c.user_id WHERE c.post_id=? ORDER BY c.id',(post,))
        QMessageBox.information(self,'Comments','\n\n'.join(f"{r['display_name']}: {r['body']}" for r in rows) or 'No comments yet.')

    def explore(self):
        self.clear_content(); self.label('Explore members · Select a member to follow/unfollow')
        self.member_search=QLineEdit(); self.member_search.setPlaceholderText('Search members…'); self.content.addWidget(self.member_search)
        self.members=QListWidget(); self.content.addWidget(self.members)
        self.member_search.textChanged.connect(self.refresh_members)
        rows=self.social.search_members(self.user['id'])
        self.member_ids=[r['id'] for r in rows]
        for r in rows: self.members.addItem(f"{r['display_name']}  @{r['username']}")
        b=QPushButton('Follow / Unfollow selected'); b.clicked.connect(self.follow); self.content.addWidget(b)
        block_btn=QPushButton('Block / Unblock selected'); block_btn.setObjectName('danger'); block_btn.clicked.connect(self.toggle_block); self.content.addWidget(block_btn)

    def refresh_members(self):
        rows=self.social.search_members(self.user['id'],self.member_search.text())
        self.member_ids=[r['id'] for r in rows]
        self.members.clear()
        for r in rows:
            self.members.addItem(f"{r['display_name']}  @{r['username']}\n{r['bio'][:100]}")

    def toggle_block(self):
        idx=self.members.currentRow()
        if idx<0:return
        target=self.member_ids[idx]; uid=self.user['id']
        if self.store.query('SELECT 1 FROM blocks WHERE blocker_id=? AND blocked_id=?',(uid,target)):
            self.store.execute('DELETE FROM blocks WHERE blocker_id=? AND blocked_id=?',(uid,target))
        else:
            with self.store.conn:
                self.store.conn.execute('INSERT INTO blocks VALUES(?,?)',(uid,target))
                self.store.conn.execute('DELETE FROM follows WHERE (follower_id=? AND following_id=?) OR (follower_id=? AND following_id=?)',(uid,target,target,uid))
        self.explore()

    def follow(self):
        idx=self.members.currentRow()
        if idx<0:return
        target=self.member_ids[idx]; uid=self.user['id']
        if self.store.query('SELECT 1 FROM blocks WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=?)',(uid,target,target,uid)):
            return QMessageBox.warning(self,'Follow','Cannot follow a blocked member.')
        if self.store.query('SELECT 1 FROM follows WHERE follower_id=? AND following_id=?',(uid,target)):
            self.store.execute('DELETE FROM follows WHERE follower_id=? AND following_id=?',(uid,target))
        else:
            self.store.execute('INSERT INTO follows VALUES(?,?)',(uid,target))
            self.store.execute('INSERT INTO notifications(user_id,body) VALUES(?,?)',(target,f"{self.user['display_name']} followed you"))
        self.explore()

    def messages(self):
        self.clear_content(); self.label('Direct messages')
        self.recipient=QLineEdit(); self.recipient.setPlaceholderText('Recipient username'); self.content.addWidget(self.recipient)
        self.message=QLineEdit(); self.message.setPlaceholderText('Write a message'); self.content.addWidget(self.message)
        b=QPushButton('Send'); b.clicked.connect(self.send_message); self.content.addWidget(b)
        rows=self.store.query('''SELECT s.username AS sender,r.username AS recipient,m.body,m.created_at FROM messages m JOIN users s ON s.id=m.sender_id JOIN users r ON r.id=m.recipient_id WHERE m.sender_id=? OR m.recipient_id=? ORDER BY m.id DESC LIMIT 50''',(self.user['id'],self.user['id']))
        history=QListWidget(); self.content.addWidget(history)
        for r in rows: history.addItem(f"{r['sender']} → {r['recipient']} · {r['created_at']}\n{r['body']}")

    def send_message(self):
        target=self.store.query('SELECT id FROM users WHERE username=?',(self.recipient.text().strip().lower(),))
        body=self.message.text().strip()
        if target and self.store.query('SELECT 1 FROM blocks WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=?)',(self.user['id'],target[0]['id'],target[0]['id'],self.user['id'])):
            return QMessageBox.warning(self,'Message','Messaging is unavailable between blocked members.')
        if not target or not body or len(body)>2000:return QMessageBox.warning(self,'Message','Valid recipient and 1–2000 characters required.')
        self.store.execute('INSERT INTO messages(sender_id,recipient_id,body) VALUES(?,?,?)',(self.user['id'],target[0]['id'],body))
        self.store.execute('INSERT INTO notifications(user_id,body) VALUES(?,?)',(target[0]['id'],f"New message from {self.user['username']}"))
        self.messages()

    def notifications(self):
        self.clear_content(); self.label('Notifications')
        for row in self.store.query('SELECT body,created_at FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 50',(self.user['id'],)):
            self.label(f"• {row['body']} · {row['created_at']}")
        self.store.execute('UPDATE notifications SET is_read=1 WHERE user_id=?',(self.user['id'],))
        self.content.addStretch()

    def profile(self):
        self.clear_content(); self.label(f"{self.user['display_name']}  @{self.user['username']}")
        stats=self.social.stats(self.user['id'])
        self.label(f"Posts: {stats['posts']}   ·   Followers: {stats['followers']}   ·   Following: {stats['following']}   ·   Saved: {stats['saved']}")
        self.bio=QTextEdit(); self.bio.setPlaceholderText('Your bio'); self.bio.setPlainText(self.user['bio']); self.bio.setMaximumHeight(100); self.content.addWidget(self.bio)
        b=QPushButton('Save profile'); b.clicked.connect(self.save_profile); self.content.addWidget(b); self.content.addStretch()

    def save_profile(self):
        if len(self.bio.toPlainText())>500:return QMessageBox.warning(self,'Profile','Bio is limited to 500 characters.')
        self.store.execute('UPDATE users SET bio=? WHERE id=?',(self.bio.toPlainText(),self.user['id']))
        self.user=self.store.query('SELECT * FROM users WHERE id=?',(self.user['id'],))[0]
        QMessageBox.information(self,'Profile','Profile saved.')

    def logout(self):
        self.user=None; self.feed_mode='all'; self.auth_screen()


def main():
    app=QApplication(sys.argv); app.setStyleSheet(STYLE)
    window=Window(); window.show()
    sys.exit(app.exec())

if __name__=='__main__':main()
