import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Calendar, 
  Plus, 
  Settings, 
  CreditCard, 
  Users, 
  Clock,
  Eye,
  Share2,
  LogOut,
  AlertCircle,
  CheckCircle2,
  Search,
  MapPin,
  UserPlus,
  Heart
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [calendars, setCalendars] = useState([]);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [friendshipRequests, setFriendshipRequests] = useState([]);
  const [locations, setLocations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvince, setSelectedProvince] = useState(user?.location?.province || '');
  const [selectedCity, setSelectedCity] = useState(user?.location?.city || '');
  const [selectedCategory, setSelectedCategory] = useState('');
  
  const [newCalendar, setNewCalendar] = useState({
    calendar_name: '',
    business_name: '',
    description: '',
    url_slug: '',
    category: 'general'
  });

  const categories = [
    { value: 'general', label: 'General' },
    { value: 'salud', label: 'Salud' },
    { value: 'belleza', label: 'Belleza' },
    { value: 'educacion', label: 'Educación' },
    { value: 'servicios', label: 'Servicios' },
    { value: 'fitness', label: 'Fitness' },
    { value: 'consultoria', label: 'Consultoría' }
  ];

  useEffect(() => {
    loadDashboardData();
    loadLocations();
    if (user?.user_type === 'employer') {
      loadFriendshipRequests();
    }
  }, []);

  useEffect(() => {
    if (user?.user_type === 'client') {
      loadCalendars();
    }
  }, [searchTerm, selectedProvince, selectedCity, selectedCategory]);

  const loadDashboardData = async () => {
    try {
      const [calendarsRes, plansRes] = await Promise.all([
        axios.get(`${API}/calendars`),
        axios.get(`${API}/subscription-plans`)
      ]);
      setCalendars(calendarsRes.data);
      setSubscriptionPlans(plansRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCalendars = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedProvince) params.append('province', selectedProvince);
      if (selectedCity) params.append('city', selectedCity);
      if (selectedCategory) params.append('category', selectedCategory);

      const response = await axios.get(`${API}/calendars?${params.toString()}`);
      setCalendars(response.data);
    } catch (error) {
      console.error('Error loading calendars:', error);
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

  const loadFriendshipRequests = async () => {
    try {
      const response = await axios.get(`${API}/friendships/requests`);
      setFriendshipRequests(response.data);
    } catch (error) {
      console.error('Error loading friendship requests:', error);
    }
  };

  const handleCreateCalendar = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/calendars`, newCalendar);
      setNewCalendar({ 
        calendar_name: '', 
        business_name: '', 
        description: '', 
        url_slug: '', 
        category: 'general' 
      });
      setShowCreateForm(false);
      loadDashboardData();
    } catch (error) {
      console.error('Error creating calendar:', error);
      alert('Error al crear el calendario: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const handleFriendshipResponse = async (friendshipId, accept) => {
    try {
      await axios.post(`${API}/friendships/${friendshipId}/respond`, { accept });
      loadFriendshipRequests();
    } catch (error) {
      console.error('Error responding to friendship:', error);
    }
  };

  const requestFriendship = async (employerId) => {
    try {
      await axios.post(`${API}/friendships/request`, { employer_id: employerId });
      alert('¡Solicitud de amistad enviada!');
      loadCalendars(); // Refresh to update UI
    } catch (error) {
      console.error('Error requesting friendship:', error);
      alert(error.response?.data?.detail || 'Error al solicitar amistad');
    }
  };

  const generateSlug = (name) => {
    return name.toLowerCase()
      .replace(/[áàäâ]/g, 'a')
      .replace(/[éèëê]/g, 'e')
      .replace(/[íìïî]/g, 'i')
      .replace(/[óòöô]/g, 'o')
      .replace(/[úùüû]/g, 'u')
      .replace(/[ñ]/g, 'n')
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  };

  const copyCalendarLink = (urlSlug) => {
    const link = `${window.location.origin}/c/${urlSlug}`;
    navigator.clipboard.writeText(link);
    alert('¡Enlace copiado al portapapeles!');
  };

  const getAvailableCities = () => {
    if (!locations || !selectedProvince) return [];
    const province = locations.argentina.provinces[selectedProvince];
    return province ? province.cities : [];
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-gray-600">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                TurnosPro
              </h1>
              <Badge variant="outline" className="text-xs">
                {user?.user_type === 'employer' ? 'Profesional' : 'Cliente'}
              </Badge>
              {user?.location && (
                <Badge variant="secondary" className="text-xs flex items-center space-x-1">
                  <MapPin className="w-3 h-3" />
                  <span>{locations?.argentina.provinces[user.location.province]?.name}, {user.location.city}</span>
                </Badge>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-gray-700 font-medium">{user?.full_name}</span>
              {friendshipRequests.length > 0 && (
                <Badge variant="destructive" className="animate-pulse">
                  {friendshipRequests.length} solicitudes
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                className="flex items-center space-x-2"
              >
                <LogOut className="w-4 h-4" />
                <span>Salir</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            ¡Bienvenido, {user?.full_name}!
          </h2>
          <p className="text-gray-600">
            {user?.user_type === 'employer' 
              ? 'Gestiona tus calendarios y configuraciones desde aquí'
              : 'Explora los profesionales disponibles y reserva tus turnos'
            }
          </p>
        </div>

        {user?.user_type === 'employer' ? (
          // Employer Dashboard
          <div className="space-y-8">
            
            {/* Friendship Requests */}
            {friendshipRequests.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <UserPlus className="w-5 h-5" />
                    <span>Solicitudes de Amistad</span>
                    <Badge variant="destructive">{friendshipRequests.length}</Badge>
                  </CardTitle>
                  <CardDescription>
                    Clientes que quieren acceder a tus calendarios
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {friendshipRequests.map((request) => (
                      <div key={request.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="space-y-1">
                          <p className="font-medium">{request.client.full_name}</p>
                          <p className="text-sm text-gray-600">{request.client.email}</p>
                          <p className="text-xs text-gray-500 flex items-center space-x-1">
                            <MapPin className="w-3 h-3" />
                            <span>
                              {locations?.argentina.provinces[request.client.location.province]?.name}, {request.client.location.city}
                            </span>
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            onClick={() => handleFriendshipResponse(request.id, true)}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            Aceptar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleFriendshipResponse(request.id, false)}
                          >
                            Rechazar
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                      <Calendar className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Calendarios</p>
                      <p className="text-2xl font-bold text-gray-900">{calendars.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Activos</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {calendars.filter(cal => cal.is_active && cal.subscription_expires && new Date(cal.subscription_expires) > new Date()).length}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                      <Heart className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Solicitudes</p>
                      <p className="text-2xl font-bold text-gray-900">{friendshipRequests.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Create Calendar Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      <Plus className="w-5 h-5" />
                      <span>Crear Nuevo Calendario</span>
                    </CardTitle>
                    <CardDescription>
                      Crea un calendario personalizado para tu negocio
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className="bg-gradient-to-r from-indigo-600 to-purple-600"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Calendario
                  </Button>
                </div>
              </CardHeader>
              
              {showCreateForm && (
                <CardContent>
                  <form onSubmit={handleCreateCalendar} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="calendar_name">Nombre del Calendario</Label>
                        <Input
                          id="calendar_name"
                          value={newCalendar.calendar_name}
                          onChange={(e) => {
                            const name = e.target.value;
                            setNewCalendar({
                              ...newCalendar,
                              calendar_name: name,
                              url_slug: generateSlug(name)
                            });
                          }}
                          placeholder="Consultas Médicas"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="business_name">Nombre del Negocio</Label>
                        <Input
                          id="business_name"
                          value={newCalendar.business_name}
                          onChange={(e) => setNewCalendar({...newCalendar, business_name: e.target.value})}
                          placeholder="Dr. Juan Pérez"
                          required
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="category">Categoría</Label>
                        <Select
                          value={newCalendar.category}
                          onValueChange={(value) => setNewCalendar({...newCalendar, category: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {categories.map((cat) => (
                              <SelectItem key={cat.value} value={cat.value}>
                                {cat.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="url_slug">URL del Calendario</Label>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">/c/</span>
                          <Input
                            id="url_slug"
                            value={newCalendar.url_slug}
                            onChange={(e) => setNewCalendar({...newCalendar, url_slug: generateSlug(e.target.value)})}
                            placeholder="dr-juan-perez"
                            required
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="description">Descripción</Label>
                      <Input
                        id="description"
                        value={newCalendar.description}
                        onChange={(e) => setNewCalendar({...newCalendar, description: e.target.value})}
                        placeholder="Consultas médicas generales"
                      />
                    </div>
                    
                    <div className="flex space-x-3">
                      <Button type="submit" className="bg-gradient-to-r from-indigo-600 to-purple-600">
                        Crear Calendario
                      </Button>
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => setShowCreateForm(false)}
                      >
                        Cancelar
                      </Button>
                    </div>
                  </form>
                </CardContent>
              )}
            </Card>

            {/* Calendars List */}
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-900">Mis Calendarios</h3>
              
              {calendars.length === 0 ? (
                <Card>
                  <CardContent className="p-12 text-center">
                    <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No tienes calendarios</h3>
                    <p className="text-gray-600 mb-6">Crea tu primer calendario para comenzar a recibir reservas</p>
                    <Button 
                      onClick={() => setShowCreateForm(true)}
                      className="bg-gradient-to-r from-indigo-600 to-purple-600"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Crear Mi Primer Calendario
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {calendars.map((calendar) => (
                    <Card key={calendar.id} className="hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{calendar.calendar_name}</CardTitle>
                            <CardDescription>{calendar.business_name}</CardDescription>
                          </div>
                          <div className="flex space-x-2">
                            <Badge variant={calendar.is_active ? "default" : "secondary"}>
                              {calendar.is_active ? "Activo" : "Inactivo"}
                            </Badge>
                            <Badge variant="outline">
                              {categories.find(c => c.value === calendar.category)?.label || calendar.category}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-600 mb-4">{calendar.description}</p>
                        
                        <div className="space-y-3">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">URL:</span>
                            <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                              /c/{calendar.url_slug}
                            </code>
                          </div>
                          
                          {calendar.subscription_expires && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Expira:</span>
                              <span className={`font-medium ${
                                new Date(calendar.subscription_expires) > new Date() 
                                  ? 'text-green-600' 
                                  : 'text-red-600'
                              }`}>
                                {new Date(calendar.subscription_expires).toLocaleDateString()}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex space-x-2 mt-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/calendar/${calendar.id}`)}
                            className="flex-1"
                          >
                            <Settings className="w-4 h-4 mr-1" />
                            Configurar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyCalendarLink(calendar.url_slug)}
                          >
                            <Share2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Subscription Plans */}
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-900">Planes de Suscripción</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {subscriptionPlans.map((plan) => (
                  <Card key={plan.id} className="text-center">
                    <CardHeader>
                      <CardTitle className="text-lg">{plan.name}</CardTitle>
                      <div className="text-3xl font-bold text-indigo-600">
                        ${plan.price_ars.toLocaleString()}
                      </div>
                      <CardDescription>{plan.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-gray-600 mb-4">
                        ✓ {plan.days} días de acceso<br/>
                        ✓ Calendarios ilimitados<br/>
                        ✓ Configuración completa
                      </div>
                      <Button className="w-full bg-gradient-to-r from-indigo-600 to-purple-600">
                        Seleccionar Plan
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Client Dashboard
          <div className="space-y-8">
            
            {/* Search and Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Search className="w-5 h-5" />
                  <span>Buscar Profesionales</span>
                </CardTitle>
                <CardDescription>
                  Encuentra profesionales en tu zona
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="search">Buscar</Label>
                    <Input
                      id="search"
                      placeholder="Nombre, servicio..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="category">Categoría</Label>
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger>
                        <SelectValue placeholder="Todas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas las categorías</SelectItem>
                        {categories.map((cat) => (
                          <SelectItem key={cat.value} value={cat.value}>
                            {cat.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="province">Provincia</Label>
                    <Select value={selectedProvince} onValueChange={(value) => {
                      setSelectedProvince(value);
                      setSelectedCity('');
                    }}>
                      <SelectTrigger>
                        <SelectValue placeholder="Tu provincia" />
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
                      value={selectedCity} 
                      onValueChange={setSelectedCity}
                      disabled={!selectedProvince}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Tu ciudad" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">Todas las ciudades</SelectItem>
                        {getAvailableCities().map((city) => (
                          <SelectItem key={city} value={city}>
                            {city}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Calendars List */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5" />
                  <span>Profesionales Disponibles</span>
                </CardTitle>
                <CardDescription>
                  Solo se muestran calendarios con suscripción activa en tu zona
                </CardDescription>
              </CardHeader>
              <CardContent>
                {calendars.length === 0 ? (
                  <div className="text-center py-8">
                    <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No hay profesionales disponibles</h3>
                    <p className="text-gray-600">Intenta cambiar los filtros de búsqueda</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {calendars.map((calendar) => (
                      <Card key={calendar.id} className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="text-lg">{calendar.business_name}</CardTitle>
                              <CardDescription>{calendar.calendar_name}</CardDescription>
                            </div>
                            <Badge variant="outline">
                              {categories.find(c => c.value === calendar.category)?.label || calendar.category}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-gray-600 mb-3">{calendar.description}</p>
                          
                          {calendar.location && (
                            <div className="flex items-center space-x-1 text-xs text-gray-500 mb-4">
                              <MapPin className="w-3 h-3" />
                              <span>
                                {locations?.argentina.provinces[calendar.location.province]?.name}, {calendar.location.city}
                              </span>
                            </div>
                          )}
                          
                          <div className="flex space-x-2">
                            <Button
                              onClick={() => window.open(`/c/${calendar.url_slug}`, '_blank')}
                              className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600"
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              Ver Calendario
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => requestFriendship(calendar.employer_id)}
                            >
                              <UserPlus className="w-4 h-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;