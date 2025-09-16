#!/usr/bin/env python3
"""
Script para crear datos de prueba en TurnosPro
"""

import requests
import json
import uuid
from datetime import datetime, timedelta, timezone

BASE_URL = "https://turnos-pro.preview.emergentagent.com/api"

def create_test_employer_and_calendar():
    """Crear empleador de prueba con calendario configurado"""
    
    # 1. Registrar empleador
    print("🔧 Creando empleador de prueba...")
    employer_email = f"demo_doctor_{uuid.uuid4().hex[:6]}@test.com"
    employer_data = {
        "email": employer_email,
        "password": "Demo123!",
        "full_name": "Dr. Juan Carlos Pérez",
        "user_type": "employer",
        "location": {
            "country": "argentina",
            "province": "chaco",
            "city": "Resistencia"
        }
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=employer_data)
    if response.status_code != 200:
        print(f"❌ Error registrando empleador: {response.status_code} - {response.text}")
        return None
    
    print(f"✅ Empleador registrado: {employer_email}")
    
    # 2. Login empleador
    login_data = {"email": employer_email, "password": "Demo123!"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Error en login: {response.status_code} - {response.text}")
        return None
    
    employer_token = response.json()["access_token"]
    print("✅ Login exitoso")
    
    # 3. Crear calendario
    calendar_slug = f"dr-juan-perez-{uuid.uuid4().hex[:6]}"
    calendar_data = {
        "calendar_name": "Consultoría Médica",
        "business_name": "Dr. Juan Carlos Pérez",
        "description": "Consultas médicas generales, medicina familiar y preventiva. Atención personalizada con años de experiencia.",
        "url_slug": calendar_slug,
        "category": "salud"
    }
    
    headers = {"Authorization": f"Bearer {employer_token}"}
    response = requests.post(f"{BASE_URL}/calendars", json=calendar_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error creando calendario: {response.status_code} - {response.text}")
        return None
    
    calendar = response.json()
    calendar_id = calendar["id"]
    print(f"✅ Calendario creado: /c/{calendar_slug}")
    
    # 4. Configurar horarios de trabajo
    settings_data = {
        "working_hours": [
            {
                "day_of_week": 0,  # Lunes
                "time_ranges": [
                    {"start_time": "08:00", "end_time": "12:00"},
                    {"start_time": "14:00", "end_time": "18:00"}
                ]
            },
            {
                "day_of_week": 1,  # Martes
                "time_ranges": [
                    {"start_time": "08:00", "end_time": "12:00"},
                    {"start_time": "14:00", "end_time": "18:00"}
                ]
            },
            {
                "day_of_week": 2,  # Miércoles
                "time_ranges": [
                    {"start_time": "08:00", "end_time": "12:00"}
                ]
            },
            {
                "day_of_week": 3,  # Jueves
                "time_ranges": [
                    {"start_time": "08:00", "end_time": "12:00"},
                    {"start_time": "14:00", "end_time": "18:00"}
                ]
            },
            {
                "day_of_week": 4,  # Viernes
                "time_ranges": [
                    {"start_time": "08:00", "end_time": "12:00"}
                ]
            }
        ],
        "blocked_dates": [],
        "blocked_saturdays": True,
        "blocked_sundays": True,
        "appointment_duration": 30,
        "buffer_time": 5
    }
    
    response = requests.put(f"{BASE_URL}/calendars/{calendar_id}/settings", json=settings_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error configurando horarios: {response.status_code} - {response.text}")
        return None
    
    print("✅ Horarios configurados")
    
    # 5. Crear cliente de prueba
    print("\n🔧 Creando cliente de prueba...")
    client_email = f"demo_client_{uuid.uuid4().hex[:6]}@test.com"
    client_data = {
        "email": client_email,
        "password": "Demo123!",
        "full_name": "María González",
        "user_type": "client",
        "location": {
            "country": "argentina",
            "province": "chaco", 
            "city": "Resistencia"
        }
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=client_data)
    if response.status_code != 200:
        print(f"❌ Error registrando cliente: {response.status_code} - {response.text}")
        return None
    
    print(f"✅ Cliente registrado: {client_email}")
    
    return {
        "employer_email": employer_email,
        "client_email": client_email,
        "calendar_slug": calendar_slug,
        "calendar_url": f"https://turnos-pro.preview.emergentagent.com/c/{calendar_slug}"
    }

def create_additional_calendars():
    """Crear calendarios adicionales para diferentes categorías"""
    
    categories = [
        {
            "name": "Dra. Ana Martínez",
            "calendar_name": "Psicología Clínica",
            "description": "Terapia psicológica individual y familiar. Especialista en ansiedad y depresión.",
            "category": "salud",
            "province": "buenos_aires",
            "city": "La Plata"
        },
        {
            "name": "Carlos Fitness Studio",
            "calendar_name": "Entrenamiento Personal",
            "description": "Sesiones de entrenamiento personalizado y planes nutricionales.",
            "category": "fitness", 
            "province": "cordoba",
            "city": "Córdoba"
        },
        {
            "name": "Beauty Salon Luna",
            "calendar_name": "Servicios de Belleza",
            "description": "Cortes de cabello, manicura, pedicura y tratamientos faciales.",
            "category": "belleza",
            "province": "santa_fe",
            "city": "Rosario"
        }
    ]
    
    results = []
    
    for cat_data in categories:
        print(f"\n🔧 Creando: {cat_data['name']}")
        
        # Registrar empleador
        employer_email = f"demo_{cat_data['category']}_{uuid.uuid4().hex[:6]}@test.com"
        employer_data = {
            "email": employer_email,
            "password": "Demo123!",
            "full_name": cat_data["name"],
            "user_type": "employer",
            "location": {
                "country": "argentina",
                "province": cat_data["province"],
                "city": cat_data["city"]
            }
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=employer_data)
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            continue
        
        # Login
        login_data = {"email": employer_email, "password": "Demo123!"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Error login: {response.status_code}")
            continue
        
        token = response.json()["access_token"]
        
        # Crear calendario
        calendar_slug = f"{cat_data['category']}-{uuid.uuid4().hex[:6]}"
        calendar_data = {
            "calendar_name": cat_data["calendar_name"],
            "business_name": cat_data["name"],
            "description": cat_data["description"],
            "url_slug": calendar_slug,
            "category": cat_data["category"]
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/calendars", json=calendar_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error calendario: {response.status_code}")
            continue
        
        calendar_id = response.json()["id"]
        
        # Configurar horarios básicos
        settings_data = {
            "working_hours": [
                {
                    "day_of_week": 0,  # Lunes
                    "time_ranges": [{"start_time": "09:00", "end_time": "17:00"}]
                },
                {
                    "day_of_week": 1,  # Martes
                    "time_ranges": [{"start_time": "09:00", "end_time": "17:00"}]
                },
                {
                    "day_of_week": 2,  # Miércoles
                    "time_ranges": [{"start_time": "09:00", "end_time": "17:00"}]
                },
                {
                    "day_of_week": 3,  # Jueves
                    "time_ranges": [{"start_time": "09:00", "end_time": "17:00"}]
                },
                {
                    "day_of_week": 4,  # Viernes
                    "time_ranges": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            ],
            "blocked_saturdays": True,
            "blocked_sundays": True,
            "appointment_duration": 60,
            "buffer_time": 0
        }
        
        response = requests.put(f"{BASE_URL}/calendars/{calendar_id}/settings", json=settings_data, headers=headers)
        if response.status_code == 200:
            results.append({
                "name": cat_data["name"],
                "email": employer_email,
                "url": f"https://turnos-pro.preview.emergentagent.com/c/{calendar_slug}"
            })
            print(f"✅ {cat_data['name']}: /c/{calendar_slug}")
        else:
            print(f"❌ Error configurando: {response.status_code}")
    
    return results

if __name__ == "__main__":
    print("🚀 Creando datos de prueba para TurnosPro\n")
    
    # Crear calendario principal
    main_result = create_test_employer_and_calendar()
    
    # Crear calendarios adicionales
    additional_results = create_additional_calendars()
    
    print("\n" + "="*60)
    print("🎉 DATOS DE PRUEBA CREADOS EXITOSAMENTE")
    print("="*60)
    
    if main_result:
        print(f"\n📋 CALENDARIO PRINCIPAL:")
        print(f"   Empleador: {main_result['employer_email']} / Demo123!")
        print(f"   Cliente: {main_result['client_email']} / Demo123!")
        print(f"   URL: {main_result['calendar_url']}")
    
    if additional_results:
        print(f"\n📋 CALENDARIOS ADICIONALES:")
        for result in additional_results:
            print(f"   {result['name']}: {result['url']}")
            print(f"      Email: {result['email']} / Demo123!")
    
    print(f"\n🔗 Puedes probar los calendarios públicos visitando las URLs mostradas")
    print(f"💡 Usa las credenciales mostradas para hacer login y probar el sistema")