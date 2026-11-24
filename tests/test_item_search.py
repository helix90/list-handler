"""Tests for GET /users/me/lists/{list_name}/items/search"""
import pytest
from fastapi import status

from app.models.list import List, ListItem


@pytest.fixture
def groceries(db_session, test_user):
    groceries = List(user_id=test_user.id, name="groceries", description="")
    db_session.add(groceries)
    db_session.commit()
    for content in ["Oat milk", "Milk chocolate", "Bread", "milk", "  Almond   MILK ", "Eggs"]:
        db_session.add(ListItem(list_id=groceries.id, content=content, is_completed=0))
    db_session.commit()
    return groceries


def search(client, headers, query, list_name="groceries"):
    return client.get(f"/users/me/lists/{list_name}/items/search", params={"q": query}, headers=headers)


class TestItemSearch:
    def test_best_match_first(self, client, auth_headers, groceries):
        response = search(client, auth_headers, "MILK")
        assert response.status_code == status.HTTP_200_OK
        # exact match, then items starting with it, then items containing it
        assert [item["content"] for item in response.json()] == ["milk", "Milk chocolate", "Oat milk", "  Almond   MILK "]

    def test_spaces_and_case_are_ignored(self, client, auth_headers, groceries):
        assert [i["content"] for i in search(client, auth_headers, "almond milk").json()] == ["  Almond   MILK "]
        assert [i["content"] for i in search(client, auth_headers, "  bread ").json()] == ["Bread"]

    def test_no_match_is_empty(self, client, auth_headers, groceries):
        response = search(client, auth_headers, "cheese")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_items_carry_their_ids(self, client, auth_headers, groceries):
        item = search(client, auth_headers, "eggs").json()[0]
        assert item["content"] == "Eggs" and isinstance(item["id"], int)

    def test_empty_query_is_rejected(self, client, auth_headers, groceries):
        assert search(client, auth_headers, "").status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_unknown_list(self, client, auth_headers, groceries):
        assert search(client, auth_headers, "milk", list_name="nope").status_code == status.HTTP_404_NOT_FOUND

    def test_only_the_owner_can_search(self, client, groceries, test_user2):
        login = client.post("/auth/login", data={"username": "testuser2", "password": "testpassword"})
        assert login.status_code == status.HTTP_200_OK, login.text
        other = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert search(client, other, "milk").status_code == status.HTTP_404_NOT_FOUND

    def test_needs_a_login(self, client, groceries):
        assert search(client, {}, "milk").status_code == status.HTTP_401_UNAUTHORIZED
