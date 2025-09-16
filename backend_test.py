import requests
import sys
import json
from datetime import datetime, timedelta, date
import uuid

class TurnosProAPITester:
    def __init__(self, base_url="https://turnos-pro.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.employer_token = None
        self.client_token = None
        self.employer_user = None
        self.client_user = None
        self.calendar_id = None
        self.calendar_slug = None
        self.friendship_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.errors.append(f"{name}: {details}")

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_employer_registration(self):
        """Test employer registration"""
        test_email = f"employer_{uuid.uuid4().hex[:8]}@test.com"
        employer_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test Employer",
            "user_type": "employer"
        }
        
        success, status, response = self.make_request('POST', 'auth/register', employer_data, expected_status=200)
        
        if success:
            self.employer_user = response
            self.log_test("Employer Registration", True)
            return True
        else:
            self.log_test("Employer Registration", False, f"Status: {status}, Response: {response}")
            return False

    def test_client_registration(self):
        """Test client registration"""
        test_email = f"client_{uuid.uuid4().hex[:8]}@test.com"
        client_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test Client",
            "user_type": "client"
        }
        
        success, status, response = self.make_request('POST', 'auth/register', client_data, expected_status=200)
        
        if success:
            self.client_user = response
            self.log_test("Client Registration", True)
            return True
        else:
            self.log_test("Client Registration", False, f"Status: {status}, Response: {response}")
            return False

    def test_employer_login(self):
        """Test employer login"""
        if not self.employer_user:
            self.log_test("Employer Login", False, "No employer user to login with")
            return False
            
        login_data = {
            "email": self.employer_user["email"],
            "password": "TestPass123!"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', login_data, expected_status=200)
        
        if success and 'access_token' in response:
            self.employer_token = response['access_token']
            self.log_test("Employer Login", True)
            return True
        else:
            self.log_test("Employer Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_client_login(self):
        """Test client login"""
        if not self.client_user:
            self.log_test("Client Login", False, "No client user to login with")
            return False
            
        login_data = {
            "email": self.client_user["email"],
            "password": "TestPass123!"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', login_data, expected_status=200)
        
        if success and 'access_token' in response:
            self.client_token = response['access_token']
            self.log_test("Client Login", True)
            return True
        else:
            self.log_test("Client Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_auth_me_employer(self):
        """Test /auth/me endpoint for employer"""
        success, status, response = self.make_request('GET', 'auth/me', token=self.employer_token, expected_status=200)
        
        if success and response.get('user_type') == 'employer':
            self.log_test("Auth Me (Employer)", True)
            return True
        else:
            self.log_test("Auth Me (Employer)", False, f"Status: {status}, Response: {response}")
            return False

    def test_auth_me_client(self):
        """Test /auth/me endpoint for client"""
        success, status, response = self.make_request('GET', 'auth/me', token=self.client_token, expected_status=200)
        
        if success and response.get('user_type') == 'client':
            self.log_test("Auth Me (Client)", True)
            return True
        else:
            self.log_test("Auth Me (Client)", False, f"Status: {status}, Response: {response}")
            return False

    def test_create_calendar(self):
        """Test calendar creation (employer only)"""
        if not self.employer_token:
            self.log_test("Create Calendar", False, "No employer token available")
            return False
            
        calendar_slug = f"test-calendar-{uuid.uuid4().hex[:8]}"
        calendar_data = {
            "calendar_name": "Test Calendar",
            "business_name": "Test Business",
            "description": "A test calendar for automated testing",
            "url_slug": calendar_slug
        }
        
        success, status, response = self.make_request('POST', 'calendars', calendar_data, token=self.employer_token, expected_status=200)
        
        if success:
            self.calendar_id = response.get('id')
            self.calendar_slug = calendar_slug
            self.log_test("Create Calendar", True)
            return True
        else:
            self.log_test("Create Calendar", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_calendars_employer(self):
        """Test getting calendars as employer"""
        success, status, response = self.make_request('GET', 'calendars', token=self.employer_token, expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Get Calendars (Employer)", True)
            return True
        else:
            self.log_test("Get Calendars (Employer)", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_calendars_client(self):
        """Test getting calendars as client"""
        success, status, response = self.make_request('GET', 'calendars', token=self.client_token, expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Get Calendars (Client)", True)
            return True
        else:
            self.log_test("Get Calendars (Client)", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_calendar_by_slug(self):
        """Test getting calendar by URL slug"""
        if not self.calendar_slug:
            self.log_test("Get Calendar by Slug", False, "No calendar slug available")
            return False
            
        success, status, response = self.make_request('GET', f'calendars/{self.calendar_slug}', expected_status=200)
        
        if success and response.get('url_slug') == self.calendar_slug:
            self.log_test("Get Calendar by Slug", True)
            return True
        else:
            self.log_test("Get Calendar by Slug", False, f"Status: {status}, Response: {response}")
            return False

    def test_update_calendar_settings(self):
        """Test updating calendar settings"""
        if not self.calendar_id or not self.employer_token:
            self.log_test("Update Calendar Settings", False, "Missing calendar ID or employer token")
            return False
            
        settings_data = {
            "working_hours": [
                {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
                {"day_of_week": 2, "start_time": "09:00", "end_time": "17:00"}
            ],
            "blocked_dates": [],
            "blocked_weekends": True,
            "blocked_days": [0, 6],
            "appointment_duration": 60,
            "buffer_time": 15
        }
        
        success, status, response = self.make_request('PUT', f'calendars/{self.calendar_id}/settings', settings_data, token=self.employer_token, expected_status=200)
        
        if success:
            self.log_test("Update Calendar Settings", True)
            return True
        else:
            self.log_test("Update Calendar Settings", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_calendar_settings(self):
        """Test getting calendar settings"""
        if not self.calendar_id:
            self.log_test("Get Calendar Settings", False, "No calendar ID available")
            return False
            
        success, status, response = self.make_request('GET', f'calendars/{self.calendar_id}/settings', expected_status=200)
        
        if success and 'calendar_id' in response:
            self.log_test("Get Calendar Settings", True)
            return True
        else:
            self.log_test("Get Calendar Settings", False, f"Status: {status}, Response: {response}")
            return False

    def test_create_appointment(self):
        """Test creating an appointment"""
        if not self.calendar_id or not self.client_token:
            self.log_test("Create Appointment", False, "Missing calendar ID or client token")
            return False
            
        # Use tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        appointment_data = {
            "appointment_date": tomorrow,
            "appointment_time": "10:00",
            "notes": "Test appointment"
        }
        
        success, status, response = self.make_request('POST', f'calendars/{self.calendar_id}/appointments', appointment_data, token=self.client_token, expected_status=200)
        
        if success:
            self.log_test("Create Appointment", True)
            return True
        else:
            self.log_test("Create Appointment", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_appointments_employer(self):
        """Test getting appointments as employer"""
        if not self.calendar_id or not self.employer_token:
            self.log_test("Get Appointments (Employer)", False, "Missing calendar ID or employer token")
            return False
            
        success, status, response = self.make_request('GET', f'calendars/{self.calendar_id}/appointments', token=self.employer_token, expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Get Appointments (Employer)", True)
            return True
        else:
            self.log_test("Get Appointments (Employer)", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_appointments_client(self):
        """Test getting appointments as client"""
        if not self.calendar_id or not self.client_token:
            self.log_test("Get Appointments (Client)", False, "Missing calendar ID or client token")
            return False
            
        success, status, response = self.make_request('GET', f'calendars/{self.calendar_id}/appointments', token=self.client_token, expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Get Appointments (Client)", True)
            return True
        else:
            self.log_test("Get Appointments (Client)", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_subscription_plans(self):
        """Test getting subscription plans"""
        success, status, response = self.make_request('GET', 'subscription-plans', expected_status=200)
        
        if success and isinstance(response, list) and len(response) > 0:
            self.log_test("Get Subscription Plans", True)
            return True
        else:
            self.log_test("Get Subscription Plans", False, f"Status: {status}, Response: {response}")
            return False

    def test_client_cannot_create_calendar(self):
        """Test that clients cannot create calendars"""
        if not self.client_token:
            self.log_test("Client Cannot Create Calendar", False, "No client token available")
            return False
            
        calendar_data = {
            "calendar_name": "Unauthorized Calendar",
            "business_name": "Should Fail",
            "description": "This should fail",
            "url_slug": "should-fail"
        }
        
        success, status, response = self.make_request('POST', 'calendars', calendar_data, token=self.client_token, expected_status=403)
        
        if success:
            self.log_test("Client Cannot Create Calendar", True)
            return True
        else:
            self.log_test("Client Cannot Create Calendar", False, f"Expected 403, got {status}: {response}")
            return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting TurnosPro API Tests...")
        print("=" * 50)
        
        # Authentication tests
        print("\n📝 Testing Authentication...")
        if not self.test_employer_registration():
            return False
        if not self.test_client_registration():
            return False
        if not self.test_employer_login():
            return False
        if not self.test_client_login():
            return False
        
        self.test_auth_me_employer()
        self.test_auth_me_client()
        
        # Calendar tests
        print("\n📅 Testing Calendar Management...")
        self.test_create_calendar()
        self.test_get_calendars_employer()
        self.test_get_calendars_client()
        self.test_get_calendar_by_slug()
        self.test_update_calendar_settings()
        self.test_get_calendar_settings()
        
        # Appointment tests
        print("\n🕐 Testing Appointments...")
        self.test_create_appointment()
        self.test_get_appointments_employer()
        self.test_get_appointments_client()
        
        # Subscription tests
        print("\n💳 Testing Subscriptions...")
        self.test_get_subscription_plans()
        
        # Authorization tests
        print("\n🔒 Testing Authorization...")
        self.test_client_cannot_create_calendar()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.errors:
            print("\n❌ Failed Tests:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TurnosProAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())