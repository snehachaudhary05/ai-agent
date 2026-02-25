"""
Supabase Configuration and Helper Functions
Handles database, auth, storage, and real-time features
"""

import os
from typing import Optional, Dict, List
from supabase import create_client, Client
from datetime import datetime
import json

class SupabaseManager:
    """Manages Supabase operations for the AI Website Builder"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not self.url or not self.key:
            print("[WARNING] Supabase credentials not configured")
            self.client = None
            self.enabled = False
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                self.enabled = True
                print("[OK] Supabase connected successfully")
            except Exception as e:
                print(f"[WARNING] Supabase connection failed: {e}")
                print("[WARNING] Continuing without Supabase...")
                self.client = None
                self.enabled = False

    def is_enabled(self) -> bool:
        """Check if Supabase is properly configured"""
        return self.enabled

    # ============================================================
    # WEBSITE METADATA OPERATIONS
    # ============================================================

    async def save_website_metadata(self, website_data: Dict) -> Optional[Dict]:
        """
        Save generated website metadata to Supabase

        Args:
            website_data: {
                'session_id': str,
                'title': str,
                'description': str,
                'deployment_url': str,
                'framework': str (e.g., 'react-vite'),
                'created_at': str,
                'last_modified': str,
                'version': int,
                'features': list,
                'status': str ('draft', 'deployed', 'archived')
            }
        """
        if not self.enabled:
            return None

        try:
            data = {
                "session_id": website_data.get("session_id"),
                "title": website_data.get("title"),
                "description": website_data.get("description"),
                "deployment_url": website_data.get("deployment_url"),
                "framework": website_data.get("framework", "react-vite"),
                "created_at": website_data.get("created_at", datetime.now().isoformat()),
                "last_modified": datetime.now().isoformat(),
                "version": website_data.get("version", 1),
                "features": json.dumps(website_data.get("features", [])),
                "status": website_data.get("status", "draft"),
                "metadata": json.dumps(website_data.get("metadata", {}))
            }

            response = self.client.table("websites").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            print(f"[ERROR] Error saving website metadata: {e}")
            return None

    async def get_website_metadata(self, session_id: str) -> Optional[Dict]:
        """Get website metadata by session ID"""
        if not self.enabled:
            return None

        try:
            response = self.client.table("websites").select("*").eq("session_id", session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[ERROR] Error fetching website metadata: {e}")
            return None

    async def update_website_metadata(self, session_id: str, updates: Dict) -> Optional[Dict]:
        """Update website metadata"""
        if not self.enabled:
            return None

        try:
            updates["last_modified"] = datetime.now().isoformat()
            response = self.client.table("websites").update(updates).eq("session_id", session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[ERROR] Error updating website metadata: {e}")
            return None

    # ============================================================
    # BOOKING OPERATIONS
    # ============================================================

    async def save_booking(self, session_id: str, booking_data: Dict) -> Optional[Dict]:
        """Save a booking submission"""
        if not self.enabled:
            return None

        try:
            data = {
                "session_id": session_id,
                "name": booking_data.get("name"),
                "email": booking_data.get("email"),
                "phone": booking_data.get("phone"),
                "service": booking_data.get("service"),
                "date": booking_data.get("date"),
                "time": booking_data.get("time"),
                "notes": booking_data.get("notes", ""),
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }

            response = self.client.table("bookings").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            print(f"[ERROR] Error saving booking: {e}")
            return None

    async def get_bookings(self, session_id: str) -> List[Dict]:
        """Get all bookings for a website"""
        if not self.enabled:
            return []

        try:
            response = self.client.table("bookings").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            print(f"[ERROR] Error fetching bookings: {e}")
            return []

    # ============================================================
    # ORDER OPERATIONS
    # ============================================================

    async def save_order(self, session_id: str, order_data: Dict) -> Optional[Dict]:
        """Save an order submission"""
        if not self.enabled:
            return None

        try:
            data = {
                "session_id": session_id,
                "name": order_data.get("name"),
                "email": order_data.get("email"),
                "phone": order_data.get("phone"),
                "address": order_data.get("address"),
                "items": json.dumps(order_data.get("items", [])),
                "total": sum(item.get("price", 0) * item.get("qty", 0) for item in order_data.get("items", [])),
                "notes": order_data.get("notes", ""),
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }

            response = self.client.table("orders").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            print(f"[ERROR] Error saving order: {e}")
            return None

    async def get_orders(self, session_id: str) -> List[Dict]:
        """Get all orders for a website"""
        if not self.enabled:
            return []

        try:
            response = self.client.table("orders").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            print(f"[ERROR] Error fetching orders: {e}")
            return []

    # ============================================================
    # CONTACT FORM OPERATIONS
    # ============================================================

    async def save_contact(self, session_id: str, contact_data: Dict) -> Optional[Dict]:
        """Save a contact form submission"""
        if not self.enabled:
            return None

        try:
            data = {
                "session_id": session_id,
                "name": contact_data.get("name"),
                "email": contact_data.get("email"),
                "phone": contact_data.get("phone", ""),
                "message": contact_data.get("message"),
                "status": "unread",
                "created_at": datetime.now().isoformat()
            }

            response = self.client.table("contacts").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            print(f"[ERROR] Error saving contact: {e}")
            return None

    async def get_contacts(self, session_id: str) -> List[Dict]:
        """Get all contact submissions for a website"""
        if not self.enabled:
            return []

        try:
            response = self.client.table("contacts").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            print(f"[ERROR] Error fetching contacts: {e}")
            return []

    # ============================================================
    # FILE STORAGE OPERATIONS
    # ============================================================

    async def upload_file(self, bucket_name: str, file_path: str, file_data: bytes) -> Optional[str]:
        """
        Upload a file to Supabase Storage

        Returns: Public URL of the uploaded file
        """
        if not self.enabled:
            return None

        try:
            response = self.client.storage.from_(bucket_name).upload(file_path, file_data)

            # Get public URL
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            return public_url

        except Exception as e:
            print(f"[ERROR] Error uploading file: {e}")
            return None

    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Delete a file from Supabase Storage"""
        if not self.enabled:
            return False

        try:
            self.client.storage.from_(bucket_name).remove([file_path])
            return True
        except Exception as e:
            print(f"[ERROR] Error deleting file: {e}")
            return False

    # ============================================================
    # AUTHENTICATION OPERATIONS
    # ============================================================

    async def sign_up_user(self, email: str, password: str) -> Optional[Dict]:
        """Sign up a new user"""
        if not self.enabled:
            return None

        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            print(f"[ERROR] Error signing up user: {e}")
            return None

    async def sign_in_user(self, email: str, password: str) -> Optional[Dict]:
        """Sign in a user"""
        if not self.enabled:
            return None

        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            print(f"[ERROR] Error signing in user: {e}")
            return None


# Global Supabase manager instance
supabase_manager = SupabaseManager()
