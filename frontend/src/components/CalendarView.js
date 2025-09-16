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
  CreditCard,
  CalendarDays
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
      alert('Error al guardar la configuración: ' + (error.response?.data?.detail || 'Error desconocido'));
    } finally {
      setSaving(false);
    }
  };

  const updateWorkingHours = (dayIndex, timeRanges) => {
    const newSettings = { ...settings };
    if (!newSettings.working_hours) {
      newSettings.working_hours = [];
    }
    
    const existingDayIndex = newSettings.working_hours.findIndex(wh => wh.day_of_week === dayIndex);
    const dayData = {
      day_of_week: dayIndex,
      time_ranges: timeRanges
    };
    
    if (existingDayIndex >= 0) {
      newSettings.working_hours[existingDayIndex] = dayData;
    } else {
      newSettings.working_hours.push(dayData);
    }
    
    setSettings(newSettings);
  };

  const addTimeRange = (dayIndex) => {
    const workingHours = getWorkingHours(dayIndex);
    const newTimeRanges = [...workingHours.time_ranges, { start_time: '09:00', end_time: '17:00' }];
    updateWorkingHours(dayIndex, newTimeRanges);
  };

  const removeTimeRange = (dayIndex, rangeIndex) => {
    const workingHours = getWorkingHours(dayIndex);
    const newTimeRanges = workingHours.time_ranges.filter((_, index) => index !== rangeIndex);
    updateWorkingHours(dayIndex, newTimeRanges);
  };

  const updateTimeRange = (dayIndex, rangeIndex, field, value) => {
    const workingHours = getWorkingHours(dayIndex);
    const newTimeRanges = [...workingHours.time_ranges];
    newTimeRanges[rangeIndex] = { ...newTimeRanges[rangeIndex], [field]: value };
    updateWorkingHours(dayIndex, newTimeRanges);
  };

  const addBlockedDate = () => {
    const dateInput = document.getElementById('blocked-date-input');
    const date = dateInput.value;
    if (date) {
      const today = new Date().toISOString().split('T')[0];
      if (date < today) {
        alert('No puedes bloquear fechas pasadas');
        return;
      }
      
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

  const addSpecificDateHours = () => {
    const dateInput = document.getElementById('specific-date-input');
    const date = dateInput.value;
    if (date) {
      const today = new Date().toISOString().split('T')[0];
      if (date < today) {
        alert('No puedes configurar horarios para fechas pasadas');
        return;
      }
      
      const newSettings = { ...settings };
      if (!newSettings.specific_date_hours) {
        newSettings.specific_date_hours = [];
      }
      
      const existingIndex = newSettings.specific_date_hours.findIndex(sd => sd.date === date);
      if (existingIndex === -1) {
        newSettings.specific_date_hours.push({
          date,
          time_ranges: [{ start_time: '09:00', end_time: '17:00' }]
        });
        setSettings(newSettings);
      }
      dateInput.value = '';
    }
  };

  const removeSpecificDate = (date) => {
    const newSettings = { ...settings };
    newSettings.specific_date_hours = newSettings.specific_date_hours.filter(sd => sd.date !== date);
    setSettings(newSettings);
  };

  const updateSpecificDateTimeRange = (date, rangeIndex, field, value) => {
    const newSettings = { ...settings };
    const dateIndex = newSettings.specific_date_hours.findIndex(sd => sd.date === date);
    if (dateIndex >= 0) {
      newSettings.specific_date_hours[dateIndex].time_ranges[rangeIndex] = {
        ...newSettings.specific_date_hours[dateIndex].time_ranges[rangeIndex],
        [field]: value
      };
      setSettings(newSettings);
    }
  };

  const addSpecificDateTimeRange = (date) => {
    const newSettings = { ...settings };
    const dateIndex = newSettings.specific_date_hours.findIndex(sd => sd.date === date);
    if (dateIndex >= 0) {
      newSettings.specific_date_hours[dateIndex].time_ranges.push({
        start_time: '09:00',
        end_time: '17:00'
      });
      setSettings(newSettings);
    }
  };

  const removeSpecificDateTimeRange = (date, rangeIndex) => {
    const newSettings = { ...settings };
    const dateIndex = newSettings.specific_date_hours.findIndex(sd => sd.date === date);
    if (dateIndex >= 0) {
      newSettings.specific_date_hours[dateIndex].time_ranges = 
        newSettings.specific_date_hours[dateIndex].time_ranges.filter((_, index) => index !== rangeIndex);
      setSettings(newSettings);
    }
  };

  const getWorkingHours = (dayIndex) => {
    if (!settings?.working_hours) return { time_ranges: [] };
    const dayHours = settings.working_hours.find(wh => wh.day_of_week === dayIndex);
    return dayHours || { time_ranges: [] };
  };

  const isBlocked = (type, dayIndex) => {
    if (!settings) return false;
    if (type === 'saturday') return settings.blocked_saturdays;
    if (type === 'sunday') return settings.blocked_sundays;
    return false;
  };

  const toggleBlockedWeekend = (type) => {
    const newSettings = { ...settings };
    if (type === 'saturday') {
      newSettings.blocked_saturdays = !newSettings.blocked_saturdays;
    } else if (type === 'sunday') {
      newSettings.blocked_sundays = !newSettings.blocked_sundays;
    }
    setSettings(newSettings);
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
            <TabsTrigger value="specific" className="flex items-center space-x-2">
              <CalendarDays className="w-4 h-4" />
              <span>Fechas Específicas</span>
            </TabsTrigger>
            <TabsTrigger value="appointments" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Turnos</span>
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

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="blocked_saturdays">Bloquear sábados</Label>
                      <p className="text-sm text-gray-600">Bloquea automáticamente todos los sábados</p>
                    </div>
                    <Switch
                      id="blocked_saturdays"
                      checked={isBlocked('saturday')}
                      onCheckedChange={() => toggleBlockedWeekend('saturday')}
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="blocked_sundays">Bloquear domingos</Label>
                      <p className="text-sm text-gray-600">Bloquea automáticamente todos los domingos</p>
                    </div>
                    <Switch
                      id="blocked_sundays"
                      checked={isBlocked('sunday')}
                      onCheckedChange={() => toggleBlockedWeekend('sunday')}
                    />
                  </div>
                </div>

                <div>
                  <Label>Fechas bloqueadas</Label>
                  <div className="flex space-x-2 mt-2">
                    <Input
                      id="blocked-date-input"
                      type="date"
                      className="flex-1"
                      min={new Date().toISOString().split('T')[0]}
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
                <CardTitle>Horarios de Trabajo Semanales</CardTitle>
                <CardDescription>
                  Configura tus horarios normales para cada día de la semana
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {daysOfWeek.map((day, index) => {
                    const workingHours = getWorkingHours(index);
                    
                    return (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium text-lg">{day}</h4>
                          <Button
                            onClick={() => addTimeRange(index)}
                            size="sm"
                            variant="outline"
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            Agregar Horario
                          </Button>
                        </div>
                        
                        {workingHours.time_ranges.length === 0 ? (
                          <p className="text-gray-500 text-sm">Sin horarios configurados</p>
                        ) : (
                          <div className="space-y-3">
                            {workingHours.time_ranges.map((range, rangeIndex) => (
                              <div key={rangeIndex} className="flex items-center space-x-3 bg-gray-50 p-3 rounded">
                                <div className="flex items-center space-x-2">
                                  <Label className="text-sm">Desde:</Label>
                                  <Input
                                    type="time"
                                    value={range.start_time}
                                    onChange={(e) => updateTimeRange(index, rangeIndex, 'start_time', e.target.value)}
                                    className="w-32"
                                  />
                                </div>
                                
                                <div className="flex items-center space-x-2">
                                  <Label className="text-sm">Hasta:</Label>
                                  <Input
                                    type="time"
                                    value={range.end_time}
                                    onChange={(e) => updateTimeRange(index, rangeIndex, 'end_time', e.target.value)}
                                    className="w-32"
                                  />
                                </div>
                                
                                <Button
                                  onClick={() => removeTimeRange(index, rangeIndex)}
                                  size="sm"
                                  variant="outline"
                                  className="text-red-600 hover:text-red-700"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            ))}
                          </div>
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

          {/* Specific Date Hours */}
          <TabsContent value="specific">
            <Card>
              <CardHeader>
                <CardTitle>Horarios para Fechas Específicas</CardTitle>
                <CardDescription>
                  Configura horarios especiales para días particulares (tienen prioridad sobre los horarios semanales)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                <div>
                  <Label>Agregar fecha específica</Label>
                  <div className="flex space-x-2 mt-2">
                    <Input
                      id="specific-date-input"
                      type="date"
                      className="flex-1"
                      min={new Date().toISOString().split('T')[0]}
                    />
                    <Button onClick={addSpecificDateHours} variant="outline">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {settings?.specific_date_hours && settings.specific_date_hours.length > 0 && (
                  <div className="space-y-6">
                    {settings.specific_date_hours.map((specificDate) => (
                      <div key={specificDate.date} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <h4 className="font-medium text-lg">
                              {new Date(specificDate.date).toLocaleDateString('es-AR', { 
                                weekday: 'long', 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                              })}
                            </h4>
                            <p className="text-sm text-gray-600">{specificDate.date}</p>
                          </div>
                          <div className="flex space-x-2">
                            <Button
                              onClick={() => addSpecificDateTimeRange(specificDate.date)}
                              size="sm"
                              variant="outline"
                            >
                              <Plus className="w-4 h-4 mr-1" />
                              Agregar Horario
                            </Button>
                            <Button
                              onClick={() => removeSpecificDate(specificDate.date)}
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="space-y-3">
                          {specificDate.time_ranges.map((range, rangeIndex) => (
                            <div key={rangeIndex} className="flex items-center space-x-3 bg-gray-50 p-3 rounded">
                              <div className="flex items-center space-x-2">
                                <Label className="text-sm">Desde:</Label>
                                <Input
                                  type="time"
                                  value={range.start_time}
                                  onChange={(e) => updateSpecificDateTimeRange(specificDate.date, rangeIndex, 'start_time', e.target.value)}
                                  className="w-32"
                                />
                              </div>
                              
                              <div className="flex items-center space-x-2">
                                <Label className="text-sm">Hasta:</Label>
                                <Input
                                  type="time"
                                  value={range.end_time}
                                  onChange={(e) => updateSpecificDateTimeRange(specificDate.date, rangeIndex, 'end_time', e.target.value)}
                                  className="w-32"
                                />
                              </div>
                              
                              <Button
                                onClick={() => removeSpecificDateTimeRange(specificDate.date, rangeIndex)}
                                size="sm"
                                variant="outline"
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <Button 
                  onClick={handleSettingsUpdate}
                  disabled={saving}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Guardando...' : 'Guardar Horarios Específicos'}
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
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-green-800 mb-2">
                      ✅ Suscripción activa hasta: {calendar?.subscription_expires ? new Date(calendar.subscription_expires).toLocaleDateString() : 'N/A'}
                    </p>
                    <p className="text-sm text-green-700">
                      Tu calendario está funcionando correctamente y puede recibir reservas.
                    </p>
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