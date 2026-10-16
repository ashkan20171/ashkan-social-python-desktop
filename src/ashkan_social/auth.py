import hashlib
import hmac
import secrets


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()


def register(store, username, display_name, password):
    username = username.strip().lower()
    if not (3 <= len(username) <= 32 and username.replace('_', '').isalnum()):
        raise ValueError('Username must be 3–32 letters, digits or underscores.')
    if not display_name.strip() or len(password) < 8:
        raise ValueError('Display name required and password must have 8+ characters.')
    salt = secrets.token_hex(16)
    return store.execute('INSERT INTO users(username,display_name,password_hash,salt) VALUES(?,?,?,?)',
                         (username, display_name.strip(), hash_password(password, salt), salt)).lastrowid


def login(store, username, password):
    rows = store.query('SELECT * FROM users WHERE username=?', (username.strip().lower(),))
    if rows and hmac.compare_digest(rows[0]['password_hash'], hash_password(password, rows[0]['salt'])):
        return rows[0]
    return None
