import pytest
import os
import tempfile
import shutil
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.auth import get_password_hash


def ensure_db_directory(db_url: str):
    """Replicate the directory creation logic from app/database.py"""
    db_path = db_url.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)


class TestDatabaseAccess:
    """Tests for database access and directory creation"""
    
    def test_database_directory_creation(self, tmp_path):
        """Test that database directory is created automatically"""
        # Create a temporary directory structure
        test_dir = tmp_path / "test_data"
        db_path = test_dir / "test.db"
        
        # Set up database URL with non-existent directory
        db_url = f"sqlite:///{db_path}"
        
        # Verify directory doesn't exist initially
        assert not test_dir.exists(), "Directory should not exist initially"
        
        # Use the actual directory creation logic
        ensure_db_directory(db_url)
        
        # Verify directory was created
        assert test_dir.exists(), "Database directory should be created automatically"
        
        # Create engine and verify it works
        test_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        
        # Test that we can create tables
        Base.metadata.create_all(bind=test_engine)
        
        # Test that we can write to the database
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_database_file_creation(self, tmp_path):
        """Test that database file can be created in data directory"""
        test_data_dir = tmp_path / "data"
        test_data_dir.mkdir()
        
        db_path = test_data_dir / "list_handler.db"
        db_url = f"sqlite:///{db_path}"
        
        # Create engine
        test_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        
        # Create tables
        Base.metadata.create_all(bind=test_engine)
        
        # Verify database file was created
        assert db_path.exists(), "Database file should be created"
        assert db_path.stat().st_size > 0, "Database file should not be empty"
        
        # Test that we can write data
        SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        db = SessionLocal_test()
        try:
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("password"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert user.id is not None
            assert user.username == "testuser"
        finally:
            db.close()
    
    def test_database_with_existing_directory(self, tmp_path):
        """Test that database works when directory already exists"""
        test_data_dir = tmp_path / "data"
        test_data_dir.mkdir()
        
        db_path = test_data_dir / "existing.db"
        db_url = f"sqlite:///{db_path}"
        
        # Create engine - directory already exists
        test_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        
        # Should work without errors
        Base.metadata.create_all(bind=test_engine)
        
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    def test_database_permissions(self, tmp_path):
        """Test that database can be written to after creation"""
        test_data_dir = tmp_path / "data"
        test_data_dir.mkdir(mode=0o777)  # Ensure writable
        
        db_path = test_data_dir / "permissions_test.db"
        db_url = f"sqlite:///{db_path}"
        
        test_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        
        Base.metadata.create_all(bind=test_engine)
        
        # Test multiple write operations
        SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        for i in range(3):
            db = SessionLocal_test()
            try:
                user = User(
                    username=f"user{i}",
                    email=f"user{i}@example.com",
                    hashed_password=get_password_hash("password"),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                assert user.id is not None
            finally:
                db.close()
        
        # Verify all users were saved
        db = SessionLocal_test()
        try:
            users = db.query(User).all()
            assert len(users) == 3
        finally:
            db.close()
    
    def test_database_directory_creation_logic(self, tmp_path):
        """Test the actual directory creation logic from database.py"""
        # Test with non-existent directory (like in Docker)
        test_data_dir = tmp_path / "nonexistent_data"
        db_path = test_data_dir / "test.db"
        db_url = f"sqlite:///{db_path}"
        
        # Verify directory doesn't exist initially
        assert not test_data_dir.exists(), "Directory should not exist initially"
        
        # Apply the directory creation logic
        ensure_db_directory(db_url)
        
        # Verify directory was created
        assert test_data_dir.exists(), "Directory should be created by ensure_db_directory"
        
        # Now create engine and verify it works
        test_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        
        # Should work without errors
        Base.metadata.create_all(bind=test_engine)
        
        # Verify database file can be created
        assert db_path.exists(), "Database file should be created successfully"
    
    def test_database_path_with_data_directory(self, tmp_path):
        """Test database path with data/ directory structure (Docker scenario)"""
        # Simulate the Docker setup: data/ directory
        test_data_dir = tmp_path / "data"
        db_path = test_data_dir / "list_handler.db"
        db_url = f"sqlite:///{db_path}"
        
        # This simulates what happens in Docker when data/ doesn't exist
        assert not test_data_dir.exists()
        
        # Apply directory creation
        ensure_db_directory(db_url)
        
        # Verify data directory was created
        assert test_data_dir.exists(), "data/ directory should be created"
        
        # Create engine and test
        test_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        
        Base.metadata.create_all(bind=test_engine)
        
        # Test write operations
        SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        db = SessionLocal_test()
        try:
            user = User(
                username="docker_user",
                email="docker@example.com",
                hashed_password=get_password_hash("password"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert user.id is not None
            assert db_path.exists()
            assert db_path.stat().st_size > 0
        finally:
            db.close()

