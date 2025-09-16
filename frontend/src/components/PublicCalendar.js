import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Calendar as CalendarIcon, Clock, User, MapPin, Phone, Mail, CheckCircle2, UserPlus, Heart, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PublicCalendar = () => {
  const { urlSlug } = useParams();
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const [calendar, setCalendar] = useState(null);
  const [settings, setSettings] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedTime, setSelectedTime] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bookingStep, setBookingStep] = useState('calendar'); // 'calendar', 'login', 'friendship', 'booking', 'success'
  const [appointmentNotes, setAppointmentNotes] = useState('');
  const [friendshipRequested, setFriendshipRequested] = useState(false);

  // Login form for guests
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ 
    email: '', 
    password: '', 
    full_name: '', 
    user_type: 'client',
    location: { country: 'argentina', province: '', city: '' }
  });
  const [isRegistering, setIsRegistering] = useState(false);
  const [authError, setAuthError] = useState('');
  const [locations, setLocations] = useState(null);

  const daysOfWeek = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    loadCalendarData();
    loadLocations();
  }, [urlSlug]);

  useEffect(() => {
    if (selectedDate) {
      loadAvailableSlots(selectedDate.toISOString().split('T')[0]);
    }
  }, [selectedDate, calendar]);

  const loadCalendarData = async () => {
    try {
      const [calendarRes, settingsRes] = await Promise.all([
        axios.get(`${API}/calendars/${urlSlug}`),
        axios.get(`${API}/calendars/${calendarRes.data.id}/settings`)
      ]);

      setCalendar(calendarRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      console.error('Error loading calendar:', error);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const loadLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`);
      setLocations(response.data);
    } catch (error) {
      console.error('Error loading locations:', error);
    }
  };

  const loadAvailableSlots = async (date) => {
    try {
      const response = await axios.get(`${API}/calendars/${calendar.id}/available-slots?date=${date}`);
      setAvailableSlots(response.data);
    } catch (error) {
      console.error('Error loading available slots:', error);
      setAvailableSlots([]);
    }
  };

  const isDateBlocked = (date) => {
    if (!settings) return false;
    
    const dateString = date.toISOString().split('T')[0];
    const dayOfWeek = date.getDay();
    
    // Check if date is specifically blocked
    if (settings.blocked_dates?.includes(dateString)) return true;
    
    // Check weekend blocks
    if (dayOfWeek === 6 && settings.blocked_saturdays) return true;
    if (dayOfWeek === 0 && settings.blocked_sundays) return true;
    
    return false;
  };

  const isDateAvailable = (date) => {
    if (!settings || !calendar) return false;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Can't book past dates
    if (date < today) return false;
    
    // Check if date is blocked
    if (isDateBlocked(date)) return false;
    
    const dayOfWeek = date.getDay();
    const dateString = date.toISOString().split('T')[0];
    
    // Check if there are specific hours for this date
    const specificHours = settings.specific_date_hours?.find(sh => sh.date === dateString);
    if (specificHours) {
      return specificHours.time_ranges && specificHours.time_ranges.length > 0;
    }
    
    // Check regular working hours
    const mondayBasedDay = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // Convert Sunday=0 to Monday=0 system
    const workingDay = settings.working_hours?.find(wh => wh.day_of_week === mondayBasedDay);
    return workingDay && workingDay.time_ranges && workingDay.time_ranges.length > 0;
  };

  const handleDateSelect = (date) => {
    if (!isDateAvailable(date)) return;
    
    setSelectedDate(date);
    setSelectedTime(null);
  };

  const handleTimeSelect = (time) => {
    setSelectedTime(time);
    if (!user) {
      setBookingStep('login');
    } else {
      // Check if friendship exists
      checkFriendshipAndProceed();
    }
  };

  const checkFriendshipAndProceed = async () => {
    try {
      // Try to create appointment directly - if friendship doesn't exist, it will fail
      setBookingStep('booking');
    } catch (error) {
      if (error.response?.status === 403) {
        setBookingStep('friendship');
      }
    }
  };

  const requestFriendship = async () => {
    try {
      await axios.post(`${API}/friendships/request`, { employer_id: calendar.employer_id });
      setFriendshipRequested(true);
    } catch (error) {
      console.error('Error requesting friendship:', error);
      alert('Error al solicitar amistad: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError('');

    if (isRegistering) {
      if (!registerData.location.province || !registerData.location.city) {
        setAuthError('Por favor selecciona tu provincia y ciudad');
        return;
      }
      
      try {
        const response = await axios.post(`${API}/auth/register`, registerData);
        if (response.status === 200) {
          // Now login
          const loginResult = await login(registerData.email, registerData.password);
          if (loginResult.success) {
            checkFriendshipAndProceed();
          } else {
            setAuthError(loginResult.error);
          }
        }
      } catch (error) {
        setAuthError(error.response?.data?.detail || 'Error al registrarse');
      }
    } else {
      const result = await login(loginData.email, loginData.password);
      if (result.success) {
        checkFriendshipAndProceed();
      } else {
        setAuthError(result.error);
      }
    }
  };

  const handleBooking = async (e) => {
    e.preventDefault();
    try {
      const appointmentData = {
        appointment_date: selectedDate.toISOString().split('T')[0],
        appointment_time: selectedTime,
        notes: appointmentNotes
      };

      await axios.post(`${API}/calendars/${calendar.id}/appointments`, appointmentData);
      setBookingStep('success');
    } catch (error) {
      console.error('Error booking appointment:', error);
      if (error.response?.status === 403) {
        setBookingStep('friendship');
      } else {
        alert('Error al reservar el turno: ' + (error.response?.data?.detail || 'Error desconocido'));
      }
    }
  };

  const renderCalendar = () => {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    const current = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      const date = new Date(current);
      const isCurrentMonth = date.getMonth() === currentMonth;
      const isToday = date.toDateString() === today.toDateString();
      const isPast = date < today && !isToday;
      const isBlocked = isDateBlocked(date);
      const isAvailable = isDateAvailable(date);
      
      let cellClass = `
        h-12 flex items-center justify-center text-sm cursor-pointer transition-all relative
        ${isCurrentMonth ? 'text-gray-900' : 'text-gray-300'}
        ${isToday ? 'bg-indigo-100 text-indigo-700 font-bold' : ''}
        ${isPast ? 'text-gray-400 cursor-not-allowed' : ''}
        ${isBlocked ? 'bg-red-100 text-red-500 cursor-not-allowed' : ''}
        ${isAvailable && !isBlocked && !isPast ? 'hover:bg-indigo-50 border-2 border-transparent hover:border-indigo-200' : ''}
        ${selectedDate?.toDateString() === date.toDateString() ? 'bg-indigo-600 text-white' : ''}
      `;
      
      days.push(
        <div
          key={i}
          className={cellClass}
          onClick={() => handleDateSelect(date)}
          title={
            isBlocked ? 'Fecha bloqueada' :
            isPast ? 'Fecha pasada' :
            !isAvailable ? 'Sin horarios disponibles' :
            'Hacer clic para seleccionar'
          }
        >
          {date.getDate()}
          {isBlocked && (
            <X className="w-3 h-3 absolute top-1 right-1 text-red-500" />
          )}
        </div>
      );
      current.setDate(current.getDate() + 1);
    }

    return days;
  };

  const getAvailableCities = () => {
    if (!locations || !registerData.location.province) return [];
    const province = locations.argentina.provinces[registerData.location.province];
    return province ? province.cities : [];
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-gray-600">Cargando calendario...</p>
        </div>
      </div>
    );
  }

  if (!calendar) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Calendario no encontrado</h2>
            <p className="text-gray-600">El calendario que buscas no existe o no está disponible.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold text-gray-900">{calendar.business_name}</h1>
            <p className="text-lg text-gray-600">{calendar.calendar_name}</p>
            {calendar.description && (
              <p className="text-gray-500">{calendar.description}</p>
            )}
            {calendar.location && (
              <div className="flex items-center justify-center space-x-1 text-sm text-gray-500">
                <MapPin className="w-4 h-4" />
                <span>
                  {locations?.argentina.provinces[calendar.location.province]?.name}, {calendar.location.city}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {bookingStep === 'calendar' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Calendar */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CalendarIcon className="w-5 h-5" />
                  <span>Selecciona una fecha</span>
                </CardTitle>
                <CardDescription>
                  Elige el día que prefieras para tu cita
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {months[new Date().getMonth()]} {new Date().getFullYear()}
                    </h3>
                  </div>
                  
                  <div className="grid grid-cols-7 gap-1">
                    {daysOfWeek.map(day => (
                      <div key={day} className="h-10 flex items-center justify-center text-sm font-medium text-gray-500">
                        {day}
                      </div>
                    ))}
                    {renderCalendar()}
                  </div>
                  
                  <div className="text-xs text-gray-500 space-y-1">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-indigo-100 border border-indigo-200 rounded"></div>
                      <span>Fechas disponibles</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-red-100 border border-red-200 rounded relative">
                        <X className="w-2 h-2 absolute inset-0 m-auto text-red-500" />
                      </div>
                      <span>Fechas bloqueadas</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gray-100 border border-gray-200 rounded"></div>
                      <span>Sin horarios disponibles</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Time Slots */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="w-5 h-5" />
                  <span>Horarios disponibles</span>
                </CardTitle>
                <CardDescription>
                  {selectedDate 
                    ? `Horarios para ${selectedDate.toLocaleDateString()}`
                    : 'Selecciona una fecha para ver los horarios'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!selectedDate ? (
                  <div className="text-center py-12">
                    <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">Selecciona una fecha primero</p>
                  </div>
                ) : availableSlots.length === 0 ? (
                  <div className="text-center py-12">
                    <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No hay horarios disponibles para esta fecha</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Select value={selectedTime || ''} onValueChange={handleTimeSelect}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Selecciona un horario" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableSlots.map((time) => (
                          <SelectItem key={time} value={time}>
                            {time}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    {selectedTime && (
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-green-800 font-medium">
                          Horario seleccionado: {selectedTime}
                        </p>
                        <p className="text-green-600 text-sm">
                          Duración: {settings?.appointment_duration || 60} minutos
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {bookingStep === 'login' && (
          <Card className="max-w-md mx-auto">
            <CardHeader>
              <CardTitle>Iniciar sesión</CardTitle>
              <CardDescription>
                Para reservar tu turno necesitas iniciar sesión o crear una cuenta
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAuth} className="space-y-4">
                {authError && (
                  <div className="p-3 text-red-700 bg-red-50 border border-red-200 rounded-lg text-sm">
                    {authError}
                  </div>
                )}

                {isRegistering && (
                  <>
                    <div>
                      <Label htmlFor="full_name">Nombre completo</Label>
                      <Input
                        id="full_name"
                        value={registerData.full_name}
                        onChange={(e) => setRegisterData({...registerData, full_name: e.target.value})}
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label htmlFor="province">Provincia</Label>
                        <Select
                          value={registerData.location.province}
                          onValueChange={(value) => setRegisterData(prev => ({
                            ...prev,
                            location: { ...prev.location, province: value, city: '' }
                          }))}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Seleccionar" />
                          </SelectTrigger>
                          <SelectContent>
                            {locations && Object.entries(locations.argentina.provinces).map(([key, province]) => (
                              <SelectItem key={key} value={key}>
                                {province.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <Label htmlFor="city">Ciudad</Label>
                        <Select
                          value={registerData.location.city}
                          onValueChange={(value) => setRegisterData(prev => ({
                            ...prev,
                            location: { ...prev.location, city: value }
                          }))}
                          disabled={!registerData.location.province}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Seleccionar" />
                          </SelectTrigger>
                          <SelectContent>
                            {getAvailableCities().map((city) => (
                              <SelectItem key={city} value={city}>
                                {city}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </>
                )}

                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={isRegistering ? registerData.email : loginData.email}
                    onChange={(e) => {
                      if (isRegistering) {
                        setRegisterData({...registerData, email: e.target.value});
                      } else {
                        setLoginData({...loginData, email: e.target.value});
                      }
                    }}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="password">Contraseña</Label>
                  <Input
                    id="password"
                    type="password"
                    value={isRegistering ? registerData.password : loginData.password}
                    onChange={(e) => {
                      if (isRegistering) {
                        setRegisterData({...registerData, password: e.target.value});
                      } else {
                        setLoginData({...loginData, password: e.target.value});
                      }
                    }}
                    required
                  />
                </div>

                <Button type="submit" className="w-full bg-gradient-to-r from-indigo-600 to-purple-600">
                  {isRegistering ? 'Crear cuenta y reservar' : 'Iniciar sesión'}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsRegistering(!isRegistering)}
                  className="w-full"
                >
                  {isRegistering ? '¿Ya tienes cuenta? Inicia sesión' : '¿No tienes cuenta? Regístrate'}
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setBookingStep('calendar')}
                  className="w-full"
                >
                  Volver al calendario
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {bookingStep === 'friendship' && (
          <Card className="max-w-md mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Heart className="w-5 h-5 text-red-500" />
                <span>Solicitud de Acceso</span>
              </CardTitle>
              <CardDescription>
                Necesitas ser autorizado por el profesional para reservar turnos
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!friendshipRequested ? (
                <>
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto">
                      <UserPlus className="w-8 h-8 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Solicitar acceso</h3>
                      <p className="text-sm text-gray-600">
                        {calendar.business_name} requiere aprobar a sus clientes antes de permitir reservas.
                      </p>
                    </div>
                  </div>
                  
                  <Button
                    onClick={requestFriendship}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600"
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Solicitar Acceso
                  </Button>
                </>
              ) : (
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto">
                    <Clock className="w-8 h-8 text-yellow-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Solicitud enviada</h3>
                    <p className="text-sm text-gray-600">
                      Tu solicitud ha sido enviada a {calendar.business_name}. 
                      Te notificaremos cuando sea aprobada.
                    </p>
                  </div>
                </div>
              )}
              
              <Button
                variant="outline"
                onClick={() => setBookingStep('calendar')}
                className="w-full"
              >
                Volver al calendario
              </Button>
            </CardContent>
          </Card>
        )}

        {bookingStep === 'booking' && (
          <Card className="max-w-md mx-auto">
            <CardHeader>
              <CardTitle>Confirmar reserva</CardTitle>
              <CardDescription>
                Revisa los detalles de tu turno
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleBooking} className="space-y-4">
                <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="w-4 h-4 text-gray-600" />
                    <span className="font-medium">{selectedDate?.toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-gray-600" />
                    <span className="font-medium">{selectedTime}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4 text-gray-600" />
                    <span>{user?.full_name}</span>
                  </div>
                </div>

                <div>
                  <Label htmlFor="notes">Notas adicionales (opcional)</Label>
                  <Textarea
                    id="notes"
                    value={appointmentNotes}
                    onChange={(e) => setAppointmentNotes(e.target.value)}
                    placeholder="Motivo de consulta, síntomas, etc."
                    rows={3}
                  />
                </div>

                <div className="flex space-x-3">
                  <Button type="submit" className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600">
                    Confirmar reserva
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setBookingStep('calendar')}
                  >
                    Volver
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {bookingStep === 'success' && (
          <Card className="max-w-md mx-auto">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">¡Reserva confirmada!</h2>
              <div className="space-y-2 text-gray-600">
                <p>Tu turno ha sido reservado exitosamente:</p>
                <div className="p-3 bg-gray-50 rounded-lg space-y-1">
                  <p><strong>Fecha:</strong> {selectedDate?.toLocaleDateString()}</p>
                  <p><strong>Hora:</strong> {selectedTime}</p>
                  <p><strong>Con:</strong> {calendar.business_name}</p>
                  <p><strong>Duración:</strong> {settings?.appointment_duration || 60} minutos</p>
                </div>
              </div>
              <p className="text-sm text-gray-500">
                Recibirás una confirmación por email. Te recomendamos llegar 10 minutos antes.
              </p>
              <Button
                onClick={() => navigate('/dashboard')}
                className="bg-gradient-to-r from-indigo-600 to-purple-600"
              >
                Ir a mi dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default PublicCalendar;