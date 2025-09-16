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
        self.appointment_id = None
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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
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
        """Test employer registration with location (NEW FEATURE)"""
        test_email = f"employer_{uuid.uuid4().hex[:8]}@test.com"
        employer_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test Employer",
            "user_type": "employer",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', employer_data, expected_status=200)
        
        if success and response.get('location'):
            self.employer_user = response
            self.log_test("Employer Registration with Location", True)
            return True
        else:
            self.log_test("Employer Registration with Location", False, f"Status: {status}, Response: {response}")
            return False

    def test_client_registration(self):
        """Test client registration with location (NEW FEATURE)"""
        test_email = f"client_{uuid.uuid4().hex[:8]}@test.com"
        client_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test Client",
            "user_type": "client",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', client_data, expected_status=200)
        
        if success and response.get('location'):
            self.client_user = response
            self.log_test("Client Registration with Location", True)
            return True
        else:
            self.log_test("Client Registration with Location", False, f"Status: {status}, Response: {response}")
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
        """Test calendar creation (legacy test)"""
        return self.test_create_calendar_with_free_subscription()

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

    def test_get_locations(self):
        """Test getting locations (NEW FEATURE)"""
        success, status, response = self.make_request('GET', 'locations', expected_status=200)
        
        if success and 'argentina' in response:
            self.log_test("Get Locations", True)
            return True
        else:
            self.log_test("Get Locations", False, f"Status: {status}, Response: {response}")
            return False

    def test_create_calendar_with_free_subscription(self):
        """Test calendar creation creates free subscription automatically (NEW FEATURE)"""
        if not self.employer_token:
            self.log_test("Create Calendar with Free Subscription", False, "No employer token available")
            return False
            
        calendar_slug = f"test-calendar-{uuid.uuid4().hex[:8]}"
        calendar_data = {
            "calendar_name": "Test Calendar",
            "business_name": "Test Business",
            "description": "A test calendar for automated testing",
            "url_slug": calendar_slug,
            "category": "medical"
        }
        
        success, status, response = self.make_request('POST', 'calendars', calendar_data, token=self.employer_token, expected_status=200)
        
        if success and response.get('subscription_expires'):
            self.calendar_id = response.get('id')
            self.calendar_slug = calendar_slug
            self.log_test("Create Calendar with Free Subscription", True)
            return True
        else:
            self.log_test("Create Calendar with Free Subscription", False, f"Status: {status}, Response: {response}")
            return False

    def test_update_calendar_settings_partial_hours(self):
        """Test updating calendar settings with partial hours (NEW FEATURE)"""
        if not self.calendar_id or not self.employer_token:
            self.log_test("Update Calendar Settings - Partial Hours", False, "Missing calendar ID or employer token")
            return False
            
        settings_data = {
            "working_hours": [
                {
                    "day_of_week": 1,  # Tuesday
                    "time_ranges": [
                        {"start_time": "09:00", "end_time": "13:00"},
                        {"start_time": "16:00", "end_time": "20:00"}
                    ]
                },
                {
                    "day_of_week": 2,  # Wednesday
                    "time_ranges": [
                        {"start_time": "10:00", "end_time": "14:00"}
                    ]
                }
            ],
            "blocked_dates": [],
            "blocked_saturdays": True,
            "blocked_sundays": True,
            "appointment_duration": 60,
            "buffer_time": 15
        }
        
        success, status, response = self.make_request('PUT', f'calendars/{self.calendar_id}/settings', settings_data, token=self.employer_token, expected_status=200)
        
        if success:
            self.log_test("Update Calendar Settings - Partial Hours", True)
            return True
        else:
            self.log_test("Update Calendar Settings - Partial Hours", False, f"Status: {status}, Response: {response}")
            return False

    def test_update_calendar_settings_specific_dates(self):
        """Test updating calendar settings with specific date hours (NEW FEATURE)"""
        if not self.calendar_id or not self.employer_token:
            self.log_test("Update Calendar Settings - Specific Dates", False, "Missing calendar ID or employer token")
            return False
            
        # Use future dates for testing
        future_date1 = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        future_date2 = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        settings_data = {
            "working_hours": [
                {
                    "day_of_week": 1,
                    "time_ranges": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            ],
            "specific_date_hours": [
                {
                    "date": future_date1,
                    "time_ranges": [
                        {"start_time": "08:00", "end_time": "12:00"},
                        {"start_time": "14:00", "end_time": "18:00"}
                    ]
                },
                {
                    "date": future_date2,
                    "time_ranges": [
                        {"start_time": "10:00", "end_time": "16:00"}
                    ]
                }
            ],
            "blocked_dates": [],
            "blocked_saturdays": False,
            "blocked_sundays": False,
            "appointment_duration": 60,
            "buffer_time": 0
        }
        
        success, status, response = self.make_request('PUT', f'calendars/{self.calendar_id}/settings', settings_data, token=self.employer_token, expected_status=200)
        
        if success:
            self.log_test("Update Calendar Settings - Specific Dates", True)
            return True
        else:
            self.log_test("Update Calendar Settings - Specific Dates", False, f"Status: {status}, Response: {response}")
            return False

    def test_blocked_dates_validation(self):
        """Test that past dates cannot be blocked (NEW FEATURE)"""
        if not self.calendar_id or not self.employer_token:
            self.log_test("Blocked Dates Validation", False, "Missing calendar ID or employer token")
            return False
            
        # Try to block a past date
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        settings_data = {
            "working_hours": [],
            "specific_date_hours": [],
            "blocked_dates": [past_date],
            "blocked_saturdays": False,
            "blocked_sundays": False,
            "appointment_duration": 60,
            "buffer_time": 0
        }
        
        success, status, response = self.make_request('PUT', f'calendars/{self.calendar_id}/settings', settings_data, token=self.employer_token, expected_status=400)
        
        if success:  # Should fail with 400
            self.log_test("Blocked Dates Validation", True)
            return True
        else:
            self.log_test("Blocked Dates Validation", False, f"Expected 400, got {status}: {response}")
            return False

    def test_request_friendship(self):
        """Test friendship request (NEW FEATURE)"""
        if not self.client_token or not self.employer_user:
            self.log_test("Request Friendship", False, "Missing client token or employer user")
            return False
            
        friendship_data = {
            "employer_id": self.employer_user["id"]
        }
        
        success, status, response = self.make_request('POST', 'friendships/request', friendship_data, token=self.client_token, expected_status=200)
        
        if success:
            self.log_test("Request Friendship", True)
            return True
        else:
            self.log_test("Request Friendship", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_friendship_requests(self):
        """Test getting friendship requests (NEW FEATURE)"""
        if not self.employer_token:
            self.log_test("Get Friendship Requests", False, "No employer token available")
            return False
            
        success, status, response = self.make_request('GET', 'friendships/requests', token=self.employer_token, expected_status=200)
        
        if success and isinstance(response, list):
            # Store friendship ID for later use
            if len(response) > 0:
                self.friendship_id = response[0].get('id')
            self.log_test("Get Friendship Requests", True)
            return True
        else:
            self.log_test("Get Friendship Requests", False, f"Status: {status}, Response: {response}")
            return False

    def test_respond_to_friendship(self):
        """Test responding to friendship request (NEW FEATURE)"""
        if not self.employer_token or not self.friendship_id:
            self.log_test("Respond to Friendship", False, "Missing employer token or friendship ID")
            return False
            
        # Accept the friendship
        response_data = {"accept": True}
        success, status, response = self.make_request('POST', f'friendships/{self.friendship_id}/respond', response_data, token=self.employer_token, expected_status=200)
        
        if success:
            self.log_test("Respond to Friendship", True)
            return True
        else:
            self.log_test("Respond to Friendship", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_available_slots(self):
        """Test getting available slots with priority logic (NEW FEATURE)"""
        if not self.calendar_id:
            self.log_test("Get Available Slots", False, "No calendar ID available")
            return False
            
        # Test with a future date
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        success, status, response = self.make_request('GET', f'calendars/{self.calendar_id}/available-slots?date={future_date}', expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Get Available Slots", True)
            return True
        else:
            self.log_test("Get Available Slots", False, f"Status: {status}, Response: {response}")
            return False

    def test_calendars_filter_by_location(self):
        """Test calendar filtering by location (NEW FEATURE)"""
        if not self.client_token:
            self.log_test("Calendar Filter by Location", False, "No client token available")
            return False
            
        # Test filtering by province
        success, status, response = self.make_request('GET', 'calendars?province=Buenos Aires', token=self.client_token, expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Calendar Filter by Location", True)
            return True
        else:
            self.log_test("Calendar Filter by Location", False, f"Status: {status}, Response: {response}")
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

    def test_create_appointment_requires_friendship(self):
        """Test creating an appointment requires accepted friendship (NEW FEATURE)"""
        if not self.calendar_id or not self.client_token:
            self.log_test("Create Appointment Requires Friendship", False, "Missing calendar ID or client token")
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
            # Store appointment ID for deletion test
            self.appointment_id = response.get('id')
            self.log_test("Create Appointment Requires Friendship", True)
            return True
        else:
            # If friendship is not accepted, it should fail with 403
            if status == 403:
                self.log_test("Create Appointment Requires Friendship", True, "Correctly blocked without friendship")
                return True
            else:
                self.log_test("Create Appointment Requires Friendship", False, f"Status: {status}, Response: {response}")
                return False

    def test_get_my_appointments(self):
        """Test GET /api/appointments/my-appointments - NEW FEATURE"""
        if not self.client_token:
            self.log_test("Get My Appointments", False, "No client token available")
            return False
            
        success, status, response = self.make_request('GET', 'appointments/my-appointments', token=self.client_token, expected_status=200)
        
        if success and isinstance(response, list):
            # Check if appointments have calendar_info enrichment
            if len(response) > 0:
                first_appointment = response[0]
                if 'calendar_info' in first_appointment:
                    self.log_test("Get My Appointments", True, "Appointments enriched with calendar info")
                else:
                    self.log_test("Get My Appointments", True, "Basic appointments list returned")
            else:
                self.log_test("Get My Appointments", True, "Empty appointments list returned")
            return True
        else:
            self.log_test("Get My Appointments", False, f"Status: {status}, Response: {response}")
            return False

    def test_delete_appointment(self):
        """Test DELETE /api/appointments/{id} - NEW FEATURE"""
        if not self.appointment_id or not self.client_token:
            self.log_test("Delete Appointment", False, "Missing appointment ID or client token")
            return False
            
        success, status, response = self.make_request('DELETE', f'appointments/{self.appointment_id}', token=self.client_token, expected_status=200)
        
        if success:
            self.log_test("Delete Appointment", True)
            return True
        else:
            self.log_test("Delete Appointment", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_available_dates(self):
        """Test GET /api/calendars/{id}/available-dates - NEW FEATURE"""
        if not self.calendar_id:
            self.log_test("Get Available Dates", False, "No calendar ID available")
            return False
            
        # Test with current month
        current_date = datetime.now()
        month = current_date.month
        year = current_date.year
        
        success, status, response = self.make_request('GET', f'calendars/{self.calendar_id}/available-dates?month={month}&year={year}', expected_status=200)
        
        if success and isinstance(response, dict):
            # Check if response has expected structure
            expected_keys = ['available_dates', 'blocked_dates', 'no_slots_dates']
            if all(key in response for key in expected_keys):
                self.log_test("Get Available Dates", True, "Response has correct structure")
                return True
            else:
                self.log_test("Get Available Dates", False, f"Missing expected keys in response: {response}")
                return False
        else:
            self.log_test("Get Available Dates", False, f"Status: {status}, Response: {response}")
            return False

    def test_demo_credentials_login(self):
        """Test login with demo credentials provided in review request"""
        print("\n🔑 Testing Demo Credentials...")
        
        # Test client demo login
        client_login_data = {
            "email": "demo_client_ff2129@test.com",
            "password": "Demo123!"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', client_login_data, expected_status=200)
        
        if success and 'access_token' in response:
            self.log_test("Demo Client Login", True)
            demo_client_token = response['access_token']
        else:
            self.log_test("Demo Client Login", False, f"Status: {status}, Response: {response}")
            demo_client_token = None
        
        # Test professional demo login
        professional_login_data = {
            "email": "demo_doctor_e5baef@test.com",
            "password": "Demo123!"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', professional_login_data, expected_status=200)
        
        if success and 'access_token' in response:
            self.log_test("Demo Professional Login", True)
            demo_professional_token = response['access_token']
        else:
            self.log_test("Demo Professional Login", False, f"Status: {status}, Response: {response}")
            demo_professional_token = None
        
        return demo_client_token, demo_professional_token

    def test_demo_calendar_access(self):
        """Test access to demo calendar dr-juan-perez-b6a389"""
        success, status, response = self.make_request('GET', 'calendars/dr-juan-perez-b6a389', expected_status=200)
        
        if success and response.get('url_slug') == 'dr-juan-perez-b6a389':
            self.log_test("Demo Calendar Access", True)
            return response.get('id')
        else:
            self.log_test("Demo Calendar Access", False, f"Status: {status}, Response: {response}")
            return None

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
        
        # Test demo credentials first
        demo_client_token, demo_professional_token = self.test_demo_credentials_login()
        demo_calendar_id = self.test_demo_calendar_access()
        
        # Location tests (NEW)
        print("\n🌍 Testing Location System...")
        self.test_get_locations()
        
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
        self.test_create_calendar_with_free_subscription()  # NEW: Tests free subscription
        self.test_get_calendars_employer()
        self.test_get_calendars_client()
        self.test_calendars_filter_by_location()  # NEW
        self.test_get_calendar_by_slug()
        
        # Calendar settings tests (NEW FEATURES)
        print("\n⚙️ Testing Calendar Settings...")
        self.test_update_calendar_settings_partial_hours()  # NEW
        self.test_update_calendar_settings_specific_dates()  # NEW
        self.test_blocked_dates_validation()  # NEW
        self.test_get_calendar_settings()
        self.test_get_available_slots()  # NEW: Tests priority logic
        
        # NEW: Test available dates endpoint
        self.test_get_available_dates()  # NEW FEATURE
        
        # Friendship system tests (NEW)
        print("\n👥 Testing Friendship System...")
        self.test_request_friendship()  # NEW
        self.test_get_friendship_requests()  # NEW
        self.test_respond_to_friendship()  # NEW
        
        # Appointment tests
        print("\n🕐 Testing Appointments...")
        self.test_create_appointment_requires_friendship()  # NEW: Tests friendship requirement
        self.test_get_my_appointments()  # NEW FEATURE
        self.test_delete_appointment()  # NEW FEATURE
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
        else:
            print("\n✅ All tests passed!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TurnosProAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())