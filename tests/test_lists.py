import pytest
from fastapi import status


class TestGetUserLists:
    """Tests for GET /users/{userId}/lists"""
    
    def test_get_lists_success(self, client, auth_headers, test_user, test_list):
        """Test getting all lists for a user"""
        response = client.get(
            "/users/me/lists",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(list_obj["id"] == test_list.id for list_obj in data)
    
    def test_get_lists_unauthorized(self, client, test_user, test_list):
        """Test getting lists without authentication"""
        response = client.get("/users/me/lists")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_lists_empty(self, client, auth_headers):
        """Test getting lists when user has no lists"""
        response = client.get(
            "/users/me/lists",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


class TestCreateList:
    """Tests for POST /users/{userId}/lists"""
    
    def test_create_list_success(self, client, auth_headers, test_user):
        """Test creating a list"""
        response = client.post(
            "/users/me/lists",
            headers=auth_headers,
            json={
                "name": "New List",
                "description": "A new list"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New List"
        assert data["description"] == "A new list"
        assert data["user_id"] == test_user.id
        assert "id" in data
    
    def test_create_list_minimal(self, client, auth_headers, test_user):
        """Test creating a list with only name"""
        response = client.post(
            "/users/me/lists",
            headers=auth_headers,
            json={"name": "Minimal List"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Minimal List"
        assert data["description"] is None
    
    def test_create_list_unauthorized(self, client, test_user):
        """Test creating a list without authentication"""
        response = client.post(
            "/users/me/lists",
            json={"name": "New List"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    


class TestGetList:
    """Tests for GET /users/{userId}/lists/{listId}"""
    
    def test_get_list_success(self, client, auth_headers, test_user, test_list):
        """Test getting a specific list with items"""
        response = client.get(
            f"/users/me/lists/{test_list.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_list.id
        assert data["name"] == test_list.name
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_get_list_not_found(self, client, auth_headers, test_user):
        """Test getting a nonexistent list"""
        response = client.get(
            "/users/me/lists/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_list_wrong_user(self, client, auth_headers, test_user, test_user2, db_session):
        """Test getting another user's list"""
        from app.models.list import List
        
        other_list = List(
            user_id=test_user2.id,
            name="Other User's List"
        )
        db_session.add(other_list)
        db_session.commit()
        db_session.refresh(other_list)
        
        response = client.get(
            f"/users/me/lists/{other_list.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateList:
    """Tests for PUT /users/{userId}/lists/{listId}"""
    
    def test_update_list_success(self, client, auth_headers, test_user, test_list):
        """Test updating a list"""
        response = client.put(
            f"/users/me/lists/{test_list.id}",
            headers=auth_headers,
            json={
                "name": "Updated List Name",
                "description": "Updated description"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated List Name"
        assert data["description"] == "Updated description"
    
    def test_update_list_partial(self, client, auth_headers, test_user, test_list):
        """Test updating only name"""
        response = client.put(
            f"/users/me/lists/{test_list.id}",
            headers=auth_headers,
            json={"name": "New Name Only"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name Only"
        # Description should remain unchanged
        assert data["description"] == test_list.description
    
    def test_update_list_not_found(self, client, auth_headers, test_user):
        """Test updating a nonexistent list"""
        response = client.put(
            "/users/me/lists/99999",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteList:
    """Tests for DELETE /users/{userId}/lists/{listId}"""
    
    def test_delete_list_success(self, client, auth_headers, test_user, db_session):
        """Test deleting a list"""
        from app.models.list import List
        
        list_to_delete = List(
            user_id=test_user.id,
            name="List to Delete"
        )
        db_session.add(list_to_delete)
        db_session.commit()
        db_session.refresh(list_to_delete)
        
        response = client.delete(
            f"/users/me/lists/{list_to_delete.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify list is deleted
        response = client.get(
            f"/users/me/lists/{list_to_delete.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_list_not_found(self, client, auth_headers, test_user):
        """Test deleting a nonexistent list"""
        response = client.delete(
            "/users/me/lists/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_list_cascades_items(self, client, auth_headers, test_user, test_list, test_list_item, db_session):
        """Test that deleting a list also deletes its items"""
        item_id = test_list_item.id
        
        response = client.delete(
            f"/users/me/lists/{test_list.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify item is also deleted
        from app.models.list import ListItem
        item = db_session.query(ListItem).filter(ListItem.id == item_id).first()
        assert item is None

