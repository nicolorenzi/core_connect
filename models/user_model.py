from sqlalchemy import Column, String, Integer, Date, Float
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime

Base = declarative_base()

class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), nullable=False, unique=True)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)

    created_at = Column("created_at", Date, default=datetime.date.today)


    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def toJSON(self):
        return {
            "id":self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat()
        }  




