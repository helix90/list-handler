import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.list import List, ListItem
from app.auth import get_password_hash, verify_password


class TestUserModel:
    """Tests for User model"""
    
    def test_create_user(self, db_session: Session):
        """Test creating a user"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert verify_password("password123", user.hashed_password)
    
    def test_user_unique_username(self, db_session: Session):
        """Test that username must be unique"""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="testuser",
            email="test2@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
    
    def test_user_unique_email(self, db_session: Session):
        """Test that email must be unique"""
        user1 = User(
            username="testuser1",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="testuser2",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


class TestListModel:
    """Tests for List model"""
    
    def test_create_list(self, db_session: Session, test_user):
        """Test creating a list"""
        list_obj = List(
            user_id=test_user.id,
            name="Shopping List",
            description="My shopping list"
        )
        db_session.add(list_obj)
        db_session.commit()
        db_session.refresh(list_obj)
        
        assert list_obj.id is not None
        assert list_obj.user_id == test_user.id
        assert list_obj.name == "Shopping List"
        assert list_obj.description == "My shopping list"
        assert list_obj.user == test_user
    
    def test_list_user_relationship(self, db_session: Session, test_user):
        """Test list-user relationship"""
        list_obj = List(
            user_id=test_user.id,
            name="Test List"
        )
        db_session.add(list_obj)
        db_session.commit()
        db_session.refresh(list_obj)
        
        assert list_obj.user.id == test_user.id
        assert list_obj in test_user.lists


class TestListItemModel:
    """Tests for ListItem model"""
    
    def test_create_list_item(self, db_session: Session, test_list):
        """Test creating a list item"""
        item = ListItem(
            list_id=test_list.id,
            content="Buy milk",
            is_completed=0
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        assert item.id is not None
        assert item.list_id == test_list.id
        assert item.content == "Buy milk"
        assert item.is_completed == 0
        assert item.list == test_list
    
    def test_list_item_list_relationship(self, db_session: Session, test_list):
        """Test list item-list relationship"""
        item = ListItem(
            list_id=test_list.id,
            content="Test Item"
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        assert item.list.id == test_list.id
        assert item in test_list.items
    
    def test_list_cascade_delete(self, db_session: Session, test_list):
        """Test that deleting a list deletes its items"""
        item1 = ListItem(
            list_id=test_list.id,
            content="Item 1"
        )
        item2 = ListItem(
            list_id=test_list.id,
            content="Item 2"
        )
        db_session.add_all([item1, item2])
        db_session.commit()
        
        list_id = test_list.id
        db_session.delete(test_list)
        db_session.commit()
        
        # Items should be deleted
        items = db_session.query(ListItem).filter(ListItem.list_id == list_id).all()
        assert len(items) == 0

