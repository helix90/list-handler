# Models package
from app.database import Base

# Import all models here so they are registered with SQLAlchemy
from app.models.user import User
from app.models.list import List, ListItem

__all__ = ["Base", "User", "List", "ListItem"]

