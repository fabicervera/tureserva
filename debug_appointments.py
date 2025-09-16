import requests
import json
import uuid

# Test the my-appointments endpoint specifically
base_url = "https://appt-view-enhance.preview.emergentagent.com/api"

def register_and_login():
    """Create test users and get tokens"""
    # Register employer
    employer_email = f"test_employer_{uuid.uuid4().hex[:8]}@test.com"
    employer_data = {
        "email": employer_email,
        "password": "TestPass123!",
        "full_name": "Test Employer Professional",
        "user_type": "employer",
        "location": {
            "country": "argentina",
            "province": "Buenos Aires",
            "city": "La Plata"
        }
    }
    
    response = requests.post(f"{base_url}/auth/register", json=employer_data)
    print(f"Employer registration: {response.status_code}")
    employer_user = response.json()
    
    # Register client
    client_email = f"test_client_{uuid.uuid4().hex[:8]}@test.com"
    client_data = {
        "email": client_email,
        "password": "TestPass123!",
        "full_name": "Test Client User",
        "user_type": "client",
        "location": {
            "country": "argentina",
            "province": "Buenos Aires",
            "city": "La Plata"
        }
    }
    
    response = requests.post(f"{base_url}/auth/register", json=client_data)
    print(f"Client registration: {response.status_code}")
    client_user = response.json()
    
    # Login employer
    response = requests.post(f"{base_url}/auth/login", json={"email": employer_email, "password": "TestPass123!"})
    employer_token = response.json()["access_token"]
    
    # Login client
    response = requests.post(f"{base_url}/auth/login", json={"email": client_email, "password": "TestPass123!"})
    client_token = response.json()["access_token"]
    
    return employer_user, client_user, employer_token, client_token

def create_calendar_and_appointment(employer_user, client_user, employer_token, client_token):
    """Create calendar, friendship, and appointment"""
    # Create calendar
    calendar_slug = f"test-calendar-{uuid.uuid4().hex[:8]}"
    calendar_data = {
        "calendar_name": "Test Professional Calendar",
        "business_name": "Test Medical Practice",
        "description": "A test calendar for professional services",
        "url_slug": calendar_slug,
        "category": "medical"
    }
    
    headers = {'Authorization': f'Bearer {employer_token}', 'Content-Type': 'application/json'}
    response = requests.post(f"{base_url}/calendars", json=calendar_data, headers=headers)
    print(f"Calendar creation: {response.status_code}")
    calendar = response.json()
    calendar_id = calendar["id"]
    
    # Request friendship
    friendship_data = {"employer_id": employer_user["id"]}
    headers = {'Authorization': f'Bearer {client_token}', 'Content-Type': 'application/json'}
    response = requests.post(f"{base_url}/friendships/request", json=friendship_data, headers=headers)
    print(f"Friendship request: {response.status_code}")
    
    # Get friendship requests
    headers = {'Authorization': f'Bearer {employer_token}', 'Content-Type': 'application/json'}
    response = requests.get(f"{base_url}/friendships/requests", headers=headers)
    friendship_requests = response.json()
    friendship_id = friendship_requests[0]["id"]
    
    # Accept friendship
    response_data = {"accept": True}
    response = requests.post(f"{base_url}/friendships/{friendship_id}/respond", json=response_data, headers=headers)
    print(f"Friendship acceptance: {response.status_code}")
    
    # Create appointment
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    appointment_data = {
        "appointment_date": tomorrow,
        "appointment_time": "10:00",
        "notes": "Test appointment for enhanced endpoint testing"
    }
    
    headers = {'Authorization': f'Bearer {client_token}', 'Content-Type': 'application/json'}
    response = requests.post(f"{base_url}/calendars/{calendar_id}/appointments", json=appointment_data, headers=headers)
    print(f"Appointment creation: {response.status_code}")
    if response.status_code != 200:
        print(f"Appointment creation error: {response.json()}")
    
    return calendar_id

def test_my_appointments(client_token):
    """Test the enhanced my-appointments endpoint"""
    headers = {'Authorization': f'Bearer {client_token}', 'Content-Type': 'application/json'}
    response = requests.get(f"{base_url}/appointments/my-appointments", headers=headers)
    
    print(f"\n=== MY APPOINTMENTS ENDPOINT TEST ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        appointments = response.json()
        print(f"Number of appointments: {len(appointments)}")
        
        if len(appointments) > 0:
            appointment = appointments[0]
            print(f"\nFirst appointment structure:")
            print(json.dumps(appointment, indent=2))
            
            # Check for required enhancements
            has_calendar_info = 'calendar_info' in appointment
            has_professional_info = 'professional_info' in appointment
            
            print(f"\n=== ENHANCEMENT CHECK ===")
            print(f"Has calendar_info: {has_calendar_info}")
            if has_calendar_info:
                print(f"Calendar info: {appointment['calendar_info']}")
            
            print(f"Has professional_info: {has_professional_info}")
            if has_professional_info:
                print(f"Professional info: {appointment['professional_info']}")
            
            if has_calendar_info and has_professional_info:
                print("✅ ENHANCEMENT SUCCESSFUL: Both calendar_info and professional_info present")
            else:
                print("❌ ENHANCEMENT FAILED: Missing required information")
        else:
            print("No appointments found")
    else:
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error (non-JSON): {response.text}")
            print(f"Status: {response.status_code}")

def main():
    print("🔍 Debugging Enhanced My-Appointments Endpoint...")
    
    # Setup test data
    employer_user, client_user, employer_token, client_token = register_and_login()
    calendar_id = create_calendar_and_appointment(employer_user, client_user, employer_token, client_token)
    
    # Test the endpoint
    test_my_appointments(client_token)

if __name__ == "__main__":
    main()