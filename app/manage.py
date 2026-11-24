"""Account administration for the List Handler API.

    python -m app.manage create-user USERNAME EMAIL     asks for the password
    python -m app.manage set-password USERNAME          asks for the new one
    python -m app.manage deactivate-user USERNAME
    python -m app.manage activate-user USERNAME
    python -m app.manage list-users

Add --password-stdin to read the password from standard input instead of
asking, e.g. in scripts. In Docker:

    docker compose exec web python -m app.manage create-user alice alice@example.com
"""
import argparse
import getpass
import sys

from email_validator import EmailNotValidError, validate_email

from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine
from app.models.user import User

MIN_PASSWORD_LENGTH = 8


def read_password(from_stdin: bool) -> str:
    if from_stdin:
        password = sys.stdin.readline().rstrip("\n")
    else:
        password = getpass.getpass("Password: ")
        if getpass.getpass("Repeat password: ") != password:
            raise SystemExit("The passwords don't match.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"The password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return password


def find_user(db, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise SystemExit(f"No user called {username!r}.")
    return user


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.manage", description="List Handler account administration")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create-user", help="create an account")
    create.add_argument("username")
    create.add_argument("email")
    create.add_argument("--password-stdin", action="store_true")

    set_password = commands.add_parser("set-password", help="change an account's password")
    set_password.add_argument("username")
    set_password.add_argument("--password-stdin", action="store_true")

    for name, help_text in (("deactivate-user", "stop an account logging in"), ("activate-user", "let an account log in again")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("username")

    commands.add_parser("list-users", help="list the accounts")

    args = parser.parse_args(argv)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.command == "create-user":
            if db.query(User).filter(User.username == args.username).first():
                raise SystemExit(f"The username {args.username!r} is taken.")
            try:
                email = validate_email(args.email, check_deliverability=False).normalized
            except EmailNotValidError as err:
                raise SystemExit(f"Invalid email: {err}")
            if db.query(User).filter(User.email == email).first():
                raise SystemExit(f"The email {email!r} is already used.")
            db.add(User(username=args.username, email=email, hashed_password=get_password_hash(read_password(args.password_stdin))))
            db.commit()
            print(f"Created user {args.username}.")
        elif args.command == "set-password":
            user = find_user(db, args.username)
            user.hashed_password = get_password_hash(read_password(args.password_stdin))
            db.commit()
            print(f"Changed the password of {args.username}.")
        elif args.command in ("deactivate-user", "activate-user"):
            user = find_user(db, args.username)
            user.is_active = args.command == "activate-user"
            db.commit()
            print(f"{args.username} is now {'active' if user.is_active else 'inactive'}.")
        elif args.command == "list-users":
            for user in db.query(User).order_by(User.username):
                print(f"{user.username}\t{user.email}\t{'active' if user.is_active else 'inactive'}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
