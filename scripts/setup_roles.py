#!/usr/bin/env python3
"""
Simple script to set up role-based system.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import db, User

def setup_roles():
    """Set up role-based system."""
    print("🔄 Setting up role-based system...")
    
    with app.app_context():
        try:
            # Update existing users with roles
            users = User.query.all()
            
            for user in users:
                if not hasattr(user, 'role') or user.role is None:
                    if user.username == 'admin':
                        user.role = 'admin'
                        print(f"   ✅ Set {user.username} as admin")
                    elif hasattr(user, 'is_admin') and getattr(user, 'is_admin', False):
                        user.role = 'admin'
                        print(f"   ✅ Set {user.username} as admin")
                    else:
                        user.role = 'viewer'  # Default role
                        print(f"   ✅ Set {user.username} as viewer")
                else:
                    print(f"   ℹ️  {user.username} already has role: {user.role}")
            
            db.session.commit()
            
            # Summary
            print("\n📊 Current Users:")
            users = User.query.all()
            for user in users:
                status = "Active" if user.is_active else "Inactive"
                print(f"   - {user.username} ({user.email}) - Role: {user.role} - Status: {status}")
            
            print("\n✅ Role-based system setup complete!")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    setup_roles()
