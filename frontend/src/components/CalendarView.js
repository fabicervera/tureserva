import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Calendar, 
  Clock, 
  Settings, 
  Users, 
  ArrowLeft,
  Plus,
  Trash2,
  Save,
  Eye,
  CreditCard
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CalendarView = () => {
  const { calendarId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [calendar, setCalendar] = useState(null);
  const [settings, setSettings] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  useEffect(() => {
    loadCalendarData();
  }, [calendarId]);

  const loadCalendarData = async () => {
    try {
      const [calendarRes, settingsRes, appointmentsRes] = await Promise.all([
        axios.get(`${API}/calendars`).then(res => res.data.find(cal => cal.id === calendarId)),
        axios.get(`${API}/calendars/${calendarId}/settings`),
        axios.get(`${API}/calendars/${calendarId}/appointments`)
      ]);

      if (!calendarRes) {
        navigate('/dashboard');
        return;
      }

      setCalendar(calendarRes);
      setSettings(settingsRes.data);
      setAppointments(appointmentsRes.data);
    } catch (error) {
      console.error('Error loading calendar data:', error);
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleSettingsUpdate = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/calendars/${calendarId}/settings`, settings);
      alert('¡Configuración guardada exitosamente!');
    } catch (error) {
      console.error('Error updating settings:', error);
      alert('Error al guardar la configuración');
    } finally {
      setSaving(false);
    }
  };

  const updateWorkingHours = (dayIndex, field, value) => {
    const newSettings = { ...settings };
    if (!newSettings.working_hours) {
      newSettings.working_hours = [];
    }
    
    const existingDay = newSettings.working_hours.find(wh => wh.day_of_week === dayIndex);
    if (existingDay) {
      existingDay[field] = value;
    } else {
      newSettings.working_hours.push({
        day_of_week: dayIndex,
        start_time: field === 'start_time' ? value : '09:00',
        end_time: field === 'end_time' ? value : '17:00'
      });
    }
    
    setSettings(newSettings);
  };

  const toggleBlockedDay = (dayIndex) => {
    const newSettings = { ...settings };
    if (!newSettings.blocked_days) {
      newSettings.blocked_days = [];
    }
    
    if (newSettings.blocked_days.includes(dayIndex)) {
      newSettings.blocked_days = newSettings.blocked_days.filter(d => d !== dayIndex);
    } else {
      newSettings.blocked_days.push(dayIndex);
    }
    
    setSettings(newSettings);
  };

  const addBlockedDate = () => {
    const dateInput = document.getElementById('blocked-date-input');
    const date = dateInput.value;
    if (date) {
      const newSettings = { ...settings };
      if (!newSettings.blocked_dates) {
        newSettings.blocked_dates = [];
      }
      if (!newSettings.blocked_dates.includes(date)) {
        newSettings.blocked_dates.push(date);
        setSettings(newSettings);
      }
      dateInput.value = '';
    }
  };

  const removeBlockedDate = (date) => {
    const newSettings = { ...settings };
    newSettings.blocked_dates = newSettings.blocked_dates.filter(d => d !== date);
    setSettings(newSettings);
  };

  const getWorkingHours = (dayIndex) => {
    if (!settings?.working_hours) return { start_time: '09:00', end_time: '17:00' };
    const dayHours = settings.working_hours.find(wh => wh.day_of_week === dayIndex);
    return dayHours || { start_time: '09:00', end_time: '17:00' };
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/dashboard')}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Volver</span>
              </Button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{calendar?.calendar_name}</h1>
                <p className="text-sm text-gray-600">{calendar?.business_name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => window.open(`/c/${calendar?.url_slug}`, '_blank')}
                className="flex items-center space-x-2"
              >
                <Eye className="w-4 h-4" />
                <span>Ver Público</span>
              </Button>
              <Badge variant={calendar?.is_active ? "default" : "secondary"}>
                {calendar?.is_active ? "Activo" : "Inactivo"}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="settings" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="settings" className="flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Configuración</span>
            </TabsTrigger>
            <TabsTrigger value="schedule" className="flex items-center space-x-2">
              <Clock className="w-4 h-4" />
              <span>Horarios</span>
            </TabsTrigger>
            <TabsTrigger value="appointments" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Turnos</span>
            </TabsTrigger>
            <TabsTrigger value="payments" className="flex items-center space-x-2">
              <CreditCard className="w-4 h-4" />
              <span>Pagos</span>
            </TabsTrigger>
          </TabsList>

          {/* General Settings */}
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>Configuración General</CardTitle>
                <CardDescription>
                  Ajusta la configuración básica de tu calendario
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="appointment_duration">Duración de turnos (minutos)</Label>
                    <Input
                      id="appointment_duration"
                      type="number"
                      value={settings?.appointment_duration || 60}
                      onChange={(e) => setSettings({...settings, appointment_duration: parseInt(e.target.value)})}
                      min="15"
                      max="240"
                      step="15"
                    />
                  </div>
                  <div>
                    <Label htmlFor="buffer_time">Tiempo entre turnos (minutos)</Label>
                    <Input
                      id="buffer_time"
                      type="number"
                      value={settings?.buffer_time || 0}
                      onChange={(e) => setSettings({...settings, buffer_time: parseInt(e.target.value)})}
                      min="0"
                      max="60"
                      step="5"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <Label htmlFor="blocked_weekends">Bloquear fines de semana</Label>
                    <p className="text-sm text-gray-600">Bloquea automáticamente sábados y domingos</p>
                  </div>
                  <Switch
                    id="blocked_weekends"
                    checked={settings?.blocked_weekends || false}
                    onCheckedChange={(checked) => setSettings({...settings, blocked_weekends: checked})}
                  />
                </div>

                <div>
                  <Label>Fechas bloqueadas</Label>
                  <div className="flex space-x-2 mt-2">
                    <Input
                      id="blocked-date-input"
                      type="date"
                      className="flex-1"
                    />
                    <Button onClick={addBlockedDate} variant="outline">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  {settings?.blocked_dates && settings.blocked_dates.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {settings.blocked_dates.map((date) => (
                        <Badge key={date} variant="secondary" className="flex items-center space-x-1">
                          <span>{new Date(date).toLocaleDateString()}</span>
                          <button onClick={() => removeBlockedDate(date)}>
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                <Button 
                  onClick={handleSettingsUpdate}
                  disabled={saving}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Guardando...' : 'Guardar Configuración'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Schedule Settings */}
          <TabsContent value="schedule">
            <Card>
              <CardHeader>
                <CardTitle>Horarios de Trabajo</CardTitle>
                <CardDescription>
                  Configura tus horarios para cada día de la semana
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {daysOfWeek.map((day, index) => {
                    const workingHours = getWorkingHours(index);
                    const isBlocked = settings?.blocked_days?.includes(index);
                    
                    return (
                      <div key={index} className="flex items-center space-x-4 p-4 border rounded-lg">
                        <div className="w-24">
                          <Label className="font-medium">{day}</Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={!isBlocked}
                            onCheckedChange={() => toggleBlockedDay(index)}
                          />
                          <span className="text-sm text-gray-600">
                            {isBlocked ? 'Bloqueado' : 'Disponible'}
                          </span>
                        </div>
                        
                        {!isBlocked && (
                          <>
                            <div className="flex items-center space-x-2">
                              <Label htmlFor={`start-${index}`} className="text-sm">Desde:</Label>
                              <Input
                                id={`start-${index}`}
                                type="time"
                                value={workingHours.start_time}
                                onChange={(e) => updateWorkingHours(index, 'start_time', e.target.value)}
                                className="w-32"
                              />
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <Label htmlFor={`end-${index}`} className="text-sm">Hasta:</Label>
                              <Input
                                id={`end-${index}`}
                                type="time"
                                value={workingHours.end_time}
                                onChange={(e) => updateWorkingHours(index, 'end_time', e.target.value)}
                                className="w-32"
                              />
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                <Button 
                  onClick={handleSettingsUpdate}
                  disabled={saving}
                  className="mt-6 bg-gradient-to-r from-indigo-600 to-purple-600"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Guardando...' : 'Guardar Horarios'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Appointments */}
          <TabsContent value="appointments">
            <Card>
              <CardHeader>
                <CardTitle>Turnos Programados</CardTitle>
                <CardDescription>
                  Gestiona todos los turnos de tu calendario
                </CardDescription>
              </CardHeader>
              <CardContent>
                {appointments.length === 0 ? (
                  <div className="text-center py-12">
                    <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No hay turnos programados</h3>
                    <p className="text-gray-600">Los turnos aparecerán aquí cuando los clientes hagan reservas</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {appointments.map((appointment) => (
                      <div key={appointment.id} className="border rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="space-y-1">
                            <h4 className="font-medium text-gray-900">{appointment.client_name}</h4>
                            <p className="text-sm text-gray-600">{appointment.client_email}</p>
                            <p className="text-sm text-gray-500">
                              {new Date(appointment.appointment_date).toLocaleDateString()} a las {appointment.appointment_time}
                            </p>
                            {appointment.notes && (
                              <p className="text-sm text-gray-600 italic">"{appointment.notes}"</p>
                            )}
                          </div>
                          <Badge variant={
                            appointment.status === 'confirmed' ? 'default' :
                            appointment.status === 'cancelled' ? 'destructive' : 'secondary'
                          }>
                            {appointment.status === 'confirmed' ? 'Confirmado' :
                             appointment.status === 'cancelled' ? 'Cancelado' : 'Completado'}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Payments */}
          <TabsContent value="payments">
            <Card>
              <CardHeader>
                <CardTitle>Configuración de MercadoPago</CardTitle>
                <CardDescription>
                  Configura tus credenciales de MercadoPago para recibir pagos
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">¿Cómo obtener las credenciales?</h4>
                    <ol className="list-decimal list-inside text-sm text-blue-800 space-y-1">
                      <li>Ingresa a tu cuenta de MercadoPago</li>
                      <li>Ve a "Desarrolladores" → "Tus integraciones"</li>
                      <li>Crea una nueva aplicación o selecciona una existente</li>
                      <li>Copia el Access Token y Public Key</li>
                    </ol>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label htmlFor="access_token">Access Token</Label>
                      <Input
                        id="access_token"
                        type="password"
                        placeholder="APP_USR-..."
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="public_key">Public Key</Label>
                      <Input
                        id="public_key"
                        type="text"
                        placeholder="APP_USR-..."
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <Button className="bg-gradient-to-r from-indigo-600 to-purple-600">
                    <Save className="w-4 h-4 mr-2" />
                    Guardar Credenciales
                  </Button>
                </div>

                <div className="mt-8 pt-6 border-t">
                  <h4 className="font-medium text-gray-900 mb-4">Estado de Suscripción</h4>
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-yellow-800">
                      ⚠️ Este calendario necesita una suscripción activa para recibir reservas.
                    </p>
                    <Button className="mt-3 bg-gradient-to-r from-yellow-500 to-orange-500">
                      Activar Suscripción
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default CalendarView;