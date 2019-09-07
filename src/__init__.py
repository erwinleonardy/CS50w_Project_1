import os

from flask import Flask, session
from flask_session import Session
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__, template_folder="./view")

# Check for environment variable
if not os.environ["DATABASE_URL"]:
	raise RuntimeError("DATABASE_URL is not set")

# Set Up Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['JSON_SORT_KEYS'] = False
Session(app)

# Set up database
engine = create_engine(os.environ["DATABASE_URL"])
db = scoped_session(sessionmaker(bind=engine))

from src.controller import routes