# check_login.py
from actions.db_actions import init_db, check_user_credentials, get_all_users
init_db()
print("Users:", get_all_users())  # (user_id, username, role)
print("Login admin/admin123 ->", bool(check_user_credentials("admin", "admin123")))
