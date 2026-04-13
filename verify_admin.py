# verify_admin.py
from actions.db_actions import init_db, force_set_admin_password, check_user_credentials

init_db()
force_set_admin_password("admin123")
print("Login admin/admin123 =>", bool(check_user_credentials("admin", "admin123")))
