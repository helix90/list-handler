import pytest
from fastapi import status
from urllib.parse import quote


class TestAuthenticationIntegration:
    """Integration tests that verify authentication flow across multiple endpoints"""
    
    def test_full_authentication_flow_across_endpoints(self, client, test_user):
        """
        Integration test: login once, use token for multiple operations.
        
        This test mimics real-world client behavior where a client:
        1. Logs in and receives a token
        2. Uses that same token to perform multiple operations
        
        This should catch issues where authentication works for some endpoints
        but fails for others (like the production bug where login + list works,
        but login + create list returns 401).
        """
        
        # Step 1: Login and get token (like real client does)
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Use that same token to list lists (this works in production)
        lists_response = client.get(
            "/users/me/lists",
            headers=headers
        )
        assert lists_response.status_code == status.HTTP_200_OK
        assert isinstance(lists_response.json(), list)
        
        # Step 3: Use that same token to create a list (this fails in production!)
        create_response = client.post(
            "/users/me/lists",
            headers=headers,
            json={"name": "New List from Integration Test"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        data = create_response.json()
        assert data["name"] == "New List from Integration Test"
        assert data["user_id"] == test_user.id
        
        # Step 4: Verify the created list appears in the list
        lists_response2 = client.get(
            "/users/me/lists",
            headers=headers
        )
        assert lists_response2.status_code == status.HTTP_200_OK
        lists = lists_response2.json()
        assert any(lst["name"] == "New List from Integration Test" for lst in lists)
    
    def test_authentication_flow_with_list_items(self, client, test_user, test_list):
        """
        Integration test for authentication across list item operations.
        
        Tests that a single login token works for creating, reading, updating,
        and deleting list items.
        """
        
        # Step 1: Login
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create an item
        create_response = client.post(
            f"/users/me/lists/{quote(test_list.name)}/items",
            headers=headers,
            json={"content": "Integration Test Item"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        item_id = create_response.json()["id"]
        
        # Step 3: Read items
        get_response = client.get(
            f"/users/me/lists/{quote(test_list.name)}/items",
            headers=headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        
        # Step 4: Update the item
        update_response = client.put(
            f"/users/me/lists/{quote(test_list.name)}/items/{item_id}",
            headers=headers,
            json={"content": "Updated Content", "is_completed": 1}
        )
        assert update_response.status_code == status.HTTP_200_OK
        
        # Step 5: Toggle completion
        toggle_response = client.patch(
            f"/users/me/lists/{quote(test_list.name)}/items/{item_id}",
            headers=headers
        )
        assert toggle_response.status_code == status.HTTP_200_OK
        
        # Step 6: Delete the item
        delete_response = client.delete(
            f"/users/me/lists/{quote(test_list.name)}/items/{item_id}",
            headers=headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_authentication_flow_list_crud_operations(self, client, test_user):
        """
        Integration test for complete CRUD operations on lists with single token.
        
        Tests creating, reading, updating, and deleting a list with one login.
        """
        
        # Step 1: Login
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create a list
        create_response = client.post(
            "/users/me/lists",
            headers=headers,
            json={"name": "CRUD Test List", "description": "Testing CRUD"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        list_id = create_response.json()["id"]
        
        # Step 3: Read the specific list
        get_response = client.get(
            f"/users/me/lists/{list_id}",
            headers=headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["name"] == "CRUD Test List"
        
        # Step 4: Update the list
        update_response = client.put(
            f"/users/me/lists/{list_id}",
            headers=headers,
            json={"name": "Updated CRUD List", "description": "Updated"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "Updated CRUD List"
        
        # Step 5: Delete the list
        delete_response = client.delete(
            f"/users/me/lists/{list_id}",
            headers=headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Step 6: Verify it's deleted
        verify_response = client.get(
            f"/users/me/lists/{list_id}",
            headers=headers
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND


class TestAuthenticationEdgeCases:
    """Tests for edge cases that might only appear in production"""
    
    def test_token_consistency_across_methods(self, client, test_user):
        """
        Test that token works identically for GET, POST, PUT, PATCH, DELETE.
        
        Some production environments have different header handling for different
        HTTP methods, especially around CORS preflight requests.
        """
        # Login once
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test GET request
        get_response = client.get(
            "/users/me/lists",
            headers=headers
        )
        assert get_response.status_code == status.HTTP_200_OK, \
            f"GET request failed with token: {get_response.status_code}"
        
        # Test POST request (this is where production fails)
        post_response = client.post(
            "/users/me/lists",
            headers=headers,
            json={"name": "Test List for Methods"}
        )
        assert post_response.status_code == status.HTTP_201_CREATED, \
            f"POST request failed with token: {post_response.status_code}, detail: {post_response.json()}"
        list_id = post_response.json()["id"]
        
        # Test PUT request
        put_response = client.put(
            f"/users/me/lists/{list_id}",
            headers=headers,
            json={"name": "Updated Name"}
        )
        assert put_response.status_code == status.HTTP_200_OK, \
            f"PUT request failed with token: {put_response.status_code}"
        
        # Test DELETE request
        delete_response = client.delete(
            f"/users/me/lists/{list_id}",
            headers=headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT, \
            f"DELETE request failed with token: {delete_response.status_code}"
    
    def test_token_with_different_content_types(self, client, test_user):
        """
        Test authentication with different Content-Type headers.
        
        Some clients might send different content types which could affect
        authentication in production environments with strict CORS policies.
        """
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        token = login_response.json()["access_token"]
        
        # Test with explicit application/json
        headers_json = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/users/me/lists",
            headers=headers_json,
            json={"name": "List with JSON content-type"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_token_whitespace_handling(self, client, test_user):
        """
        Test that token parsing handles whitespace correctly.
        
        Some clients might add extra whitespace in the Authorization header.
        """
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        token = login_response.json()["access_token"]
        
        # Test with extra spaces (FastAPI should handle this, but good to verify)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/users/me/lists",
            headers=headers,
            json={"name": "Test whitespace handling"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_sequential_operations_same_token(self, client, test_user):
        """
        Test multiple operations in rapid succession with the same token.
        
        This mimics real client behavior where multiple API calls are made
        quickly with the same token. Tests for token expiry or reuse issues.
        """
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Perform 5 create operations in rapid succession
        list_ids = []
        for i in range(5):
            response = client.post(
                "/users/me/lists",
                headers=headers,
                json={"name": f"Rapid List {i}"}
            )
            assert response.status_code == status.HTTP_201_CREATED, \
                f"Failed on iteration {i}: {response.status_code}"
            list_ids.append(response.json()["id"])
        
        # Verify all lists were created
        response = client.get(
            "/users/me/lists",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        created_names = [lst["name"] for lst in response.json()]
        for i in range(5):
            assert f"Rapid List {i}" in created_names
    
    def test_login_then_immediate_post(self, client, test_user):
        """
        Test the exact sequence that fails in production:
        1. Login
        2. Immediately create a list
        
        No other operations in between.
        """
        # Step 1: Login
        login_response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        token = token_data["access_token"]
        
        # Step 2: Immediately try to create a list (this fails in production)
        create_response = client.post(
            "/users/me/lists",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Immediate Post Test"}
        )
        
        # This should succeed but fails in production with 401
        assert create_response.status_code == status.HTTP_201_CREATED, \
            f"Expected 201, got {create_response.status_code}. Response: {create_response.json() if create_response.status_code != 500 else 'Server error'}"

