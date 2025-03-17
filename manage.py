from flask.cli import FlaskGroup
import getpass

from src import app, db, bcrypt
from src.account.models import User

cli = FlaskGroup(app)
    
@cli.command("create_admin")
def create_admin():
    """Creates the admin user."""
    exist_admin=User.query.filter_by(is_admin=True)
    if exist_admin.count()!=0:
        print("Admin user already exists!")
        return 2
    email = input("Enter email address: ")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Enter password again: ")
    if password != confirm_password:
        print("Passwords don't match")
        return 1
    try:
        user = User(username="admin", email=email, password=bcrypt.generate_password_hash(password), is_admin=True)
        db.session.add(user)
        db.session.commit()
        print("Successfully create admin user. Remember, the username is: admin.")
    except Exception:
        print("Couldn't create admin user.")

        
@cli.command("remove_user")
def remove_admin():
    email = input("Enter Username: ")
    try:
        user = User.query.filter_by(username=email).first()
        db.session.delete(user)
        db.session.commit()
        print("Successfully remove user.")
    except Exception:
        print("Couldn't remove user.")

@cli.command("unlock")
def unlock():
    email = input("Enter Username: ")
    user = User.query.filter_by(username=email).first()
    if user.is_locked == False:
        print("User not locked.")
        return 1
    try:
        user.is_locked = False
        db.session.commit()
        print("Successfully unlocked user.")
    except Exception:
        print("Couldn't unlocke user.")

if __name__ == "__main__":
    cli()