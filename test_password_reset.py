"""
Test password reset functionality.
"""
import requests
import json

API_BASE = "http://127.0.0.1:5050"

def test_password_reset():
    """Test password reset endpoint."""
    print("=" * 60)
    print("Testing Password Reset")
    print("=" * 60)
    
    # Test email (use your actual email)
    test_email = input("Enter email to test password reset: ").strip()
    
    if not test_email:
        print("No email provided, skipping test")
        return
    
    print(f"\n[TEST] Requesting password reset for: {test_email}")
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/forgot-password",
            json={"email": test_email},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"[TEST] Status Code: {response.status_code}")
        print(f"[TEST] Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("\n[SUCCESS] Password reset request successful!")
                if data.get("token"):
                    print(f"[INFO] Reset token: {data.get('token')}")
                    print(f"[INFO] Reset URL: {data.get('reset_url')}")
                if data.get("email_sent"):
                    print("[INFO] Email was sent")
                if data.get("sms_sent"):
                    print("[INFO] SMS was sent")
                if not data.get("email_sent") and not data.get("sms_sent"):
                    print("[INFO] Email/SMS not configured - token shown for development")
            else:
                print(f"\n[ERROR] Request failed: {data.get('error')}")
        else:
            print(f"\n[ERROR] HTTP {response.status_code}: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to server. Is it running?")
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")

if __name__ == "__main__":
    test_password_reset()

