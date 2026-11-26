"""Lists are found by the name as people type or say it"""
from urllib.parse import quote

import pytest
from fastapi import status

from app.lookup import loose_name


@pytest.mark.parametrize("typed,expected", [
    ("groceries", "grocery"),
    ("Groceries", "grocery"),
    ("my groceries list", "grocery"),
    ("the  Grocery List", "grocery"),
    ("boxes", "box"),
    ("dishes", "dish"),
    ("glass", "glass"),
    ("bus", "bus"),
    ("to do", "to do"),
    ("list", "list"),
    ("todos", "todo"),
])
def test_loose_name(typed, expected):
    assert loose_name(typed) == expected


def make(client, headers, name):
    response = client.post("/users/me/lists", headers=headers, json={"name": name})
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("typed", ["groceries", "Groceries", "GROCERIES", "grocery", "my groceries list", "Groceries List"])
def test_get_list_by_loose_name(client, auth_headers, typed):
    make(client, auth_headers, "Groceries")
    response = client.get(f"/users/me/lists/{quote(typed)}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Groceries"


def test_items_by_loose_name(client, auth_headers):
    make(client, auth_headers, "groceries")
    response = client.post("/users/me/lists/Grocery/items", headers=auth_headers, json={"content": "milk"})
    assert response.status_code == status.HTTP_201_CREATED
    items = client.get("/users/me/lists/groceries/items", headers=auth_headers).json()
    assert [item["content"] for item in items] == ["milk"]


def test_exact_name_wins(client, auth_headers):
    make(client, auth_headers, "Books")
    make(client, auth_headers, "books")
    make(client, auth_headers, "book")
    for typed in ["Books", "books", "book"]:
        response = client.get(f"/users/me/lists/{typed}", headers=auth_headers)
        assert response.json()["name"] == typed


def test_case_beats_loose(client, auth_headers):
    make(client, auth_headers, "Book")
    make(client, auth_headers, "BOOKS")
    assert client.get("/users/me/lists/books", headers=auth_headers).json()["name"] == "BOOKS"


def test_unknown_name_is_not_found(client, auth_headers):
    make(client, auth_headers, "groceries")
    for typed in ["gro", "hardware", "grocery store"]:
        response = client.get(f"/users/me/lists/{quote(typed)}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_other_users_lists_are_not_found(client, auth_headers, test_user2, db_session):
    from app.models.list import List
    db_session.add(List(user_id=test_user2.id, name="Groceries"))
    db_session.commit()
    assert client.get("/users/me/lists/groceries", headers=auth_headers).status_code == status.HTTP_404_NOT_FOUND


def test_delete_by_loose_name(client, auth_headers):
    make(client, auth_headers, "Chores")
    assert client.delete("/users/me/lists/chore", headers=auth_headers).status_code == status.HTTP_204_NO_CONTENT
    assert client.get("/users/me/lists", headers=auth_headers).json() == []
