"""Finding a user's list by the name someone typed or said.

Names are matched exactly first, then ignoring case, then loosely: a
leading "my", "the" or "our", a trailing "list" and plurals are ignored, so
"Groceries", "grocery" and "my groceries list" all find "groceries".
"""
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.list import List
from app.models.user import User

_LEADING = re.compile(r"^(?:my|the|our)\s+")
_TRAILING = re.compile(r"\s+list$")


def _singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and re.search(r"(?:s|x|z|ch|sh)es$", word):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def loose_name(name: str) -> str:
    """The form of a list name that loose matching compares"""
    name = " ".join(name.casefold().split())
    name = _LEADING.sub("", name)
    if name != "list":
        name = _TRAILING.sub("", name)
    words = name.split(" ")
    words[-1] = _singular(words[-1])
    return " ".join(words)


def find_user_list(db: Session, user: User, name: str) -> Optional[List]:
    """The user's list called name, or None"""
    exact = db.query(List).filter(List.user_id == user.id, List.name == name).first()
    if exact:
        return exact
    lists = db.query(List).filter(List.user_id == user.id).order_by(List.id).all()
    folded = name.casefold()
    for candidate in lists:
        if candidate.name.casefold() == folded:
            return candidate
    loose = loose_name(name)
    for candidate in lists:
        if loose_name(candidate.name) == loose:
            return candidate
    return None
