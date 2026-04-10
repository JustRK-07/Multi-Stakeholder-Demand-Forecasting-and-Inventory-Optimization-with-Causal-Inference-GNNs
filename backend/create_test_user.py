"""
Script to create a test user for quick demo access
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Initialize database FIRST
from app.database import init_db
database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
init_db(database_url)

# Now import auth
from app.auth_store import create_user

try:
    result = create_user(
        name="Rushabh",
        email="rushabh@retailcast.com",
        password="Rushabh@123",
        store_type="grocery"
    )
    print("\n✅ Test user created successfully!\n")
    print("📧 Login Credentials:")
    print("   Email: rushabh@retailcast.com")
    print("   Password: Rushabh@123\n")
    print("🏪 Account Details:")
    print("   Name: Rushabh")
    print("   Store Type: Grocery")
    print("   Model: model-grocery-v1.0\n")
    print("✨ Visit: http://localhost:3000/login\n")
    
except Exception as e:
    error_str = str(e)
    if "already exists" in error_str or "UNIQUE constraint failed" in error_str:
        print("\n⚠️  User already exists!\n")
        print("📧 Credentials:")
        print("   Email: rushabh@retailcast.com")
        print("   Password: Rushabh@123\n")
        print("✨ Visit: http://localhost:3000/login\n")
    else:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
