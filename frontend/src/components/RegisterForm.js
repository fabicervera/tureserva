import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { AlertCircle, CheckCircle, User, Briefcase, MapPin } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    user_type: 'client',
    location: {
      country: 'argentina',
      province: '',
      city: ''
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [locations, setLocations] = useState(null);
  const [availableCities, setAvailableCities] = useState([]);
  const { register } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadLocations();
  }, []);

  useEffect(() => {
    if (formData.location.province && locations) {
      const province = locations.argentina.provinces[formData.location.province];
      setAvailableCities(province ? province.cities : []);
      // Reset city when province changes
      setFormData(prev => ({
        ...prev,
        location: { ...prev.location, city: '' }
      }));
    }
  }, [formData.location.province, locations]);

  const loadLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`);
      setLocations(response.data);
    } catch (error) {
      console.error('Error loading locations:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!formData.location.province || !formData.location.city) {
      setError('Por favor selecciona tu provincia y ciudad');
      setLoading(false);
      return;
    }

    const result = await register(formData);
    
    if (result.success) {
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md bg-white/80 backdrop-blur-xl border-white/20 shadow-2xl">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">¡Registro Exitoso!</h2>
              <p className="text-gray-600">
                Tu cuenta ha sido creada correctamente. Serás redirigido al inicio de sesión.
              </p>
              <div className="w-8 h-8 border-4 border-green-200 border-t-green-600 rounded-full animate-spin mx-auto"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl flex items-center justify-center gap-8">
        
        {/* Left side - Info */}
        <div className="hidden lg:block max-w-md space-y-6">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Únete a TurnosPro
            </h1>
            <p className="text-lg text-gray-600">
              Crea tu cuenta y comienza a gestionar turnos de manera profesional
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                <User className="w-4 h-4 text-indigo-600" />
              </div>
              <span className="text-gray-700">Para clientes que buscan reservar turnos</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <Briefcase className="w-4 h-4 text-purple-600" />
              </div>
              <span className="text-gray-700">Para profesionales que ofrecen servicios</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <MapPin className="w-4 h-4 text-green-600" />
              </div>
              <span className="text-gray-700">Conecta con profesionales de tu zona</span>
            </div>
          </div>
        </div>

        {/* Right side - Register form */}
        <div className="w-full max-w-md">
          <Card className="bg-white/80 backdrop-blur-xl border-white/20 shadow-2xl">
            <CardHeader className="space-y-1 text-center">
              <CardTitle className="text-3xl font-bold text-gray-900">Crear Cuenta</CardTitle>
              <CardDescription className="text-gray-600">
                Completa los datos para registrarte
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="flex items-center space-x-2 p-3 text-red-700 bg-red-50 border border-red-200 rounded-lg">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="full_name" className="text-sm font-medium text-gray-700">
                    Nombre completo
                  </Label>
                  <Input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                    className="h-12 px-4 bg-white/50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-400/20"
                    placeholder="Juan Pérez"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                    Correo electrónico
                  </Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="h-12 px-4 bg-white/50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-400/20"
                    placeholder="tu@email.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                    Contraseña
                  </Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="h-12 px-4 bg-white/50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-400/20"
                    placeholder="••••••••"
                  />
                </div>

                {/* Location Selection */}
                <div className="space-y-4">
                  <Label className="text-sm font-medium text-gray-700 flex items-center space-x-2">
                    <MapPin className="w-4 h-4" />
                    <span>Ubicación</span>
                  </Label>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="province" className="text-xs text-gray-600">Provincia</Label>
                      <Select
                        value={formData.location.province}
                        onValueChange={(value) => setFormData(prev => ({
                          ...prev,
                          location: { ...prev.location, province: value }
                        }))}
                      >
                        <SelectTrigger className="h-11 bg-white/50">
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
                      <Label htmlFor="city" className="text-xs text-gray-600">Ciudad</Label>
                      <Select
                        value={formData.location.city}
                        onValueChange={(value) => setFormData(prev => ({
                          ...prev,
                          location: { ...prev.location, city: value }
                        }))}
                        disabled={!formData.location.province}
                      >
                        <SelectTrigger className="h-11 bg-white/50">
                          <SelectValue placeholder="Seleccionar" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableCities.map((city) => (
                            <SelectItem key={city} value={city}>
                              {city}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-medium text-gray-700">Tipo de cuenta</Label>
                  <RadioGroup
                    value={formData.user_type}
                    onValueChange={(value) => setFormData(prev => ({...prev, user_type: value}))}
                    className="space-y-3"
                  >
                    <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                      <RadioGroupItem value="client" id="client" />
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <User className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <Label htmlFor="client" className="font-medium text-gray-900 cursor-pointer">
                            Cliente
                          </Label>
                          <p className="text-sm text-gray-600">Quiero reservar turnos</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                      <RadioGroupItem value="employer" id="employer" />
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                          <Briefcase className="w-4 h-4 text-purple-600" />
                        </div>
                        <div>
                          <Label htmlFor="employer" className="font-medium text-gray-900 cursor-pointer">
                            Profesional
                          </Label>
                          <p className="text-sm text-gray-600">Quiero ofrecer mis servicios</p>
                        </div>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium rounded-xl transition duration-300 shadow-lg hover:shadow-xl"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Creando cuenta...</span>
                    </div>
                  ) : (
                    'Crear Cuenta'
                  )}
                </Button>

                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    ¿Ya tienes cuenta?{' '}
                    <Link 
                      to="/login" 
                      className="font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
                    >
                      Iniciar sesión
                    </Link>
                  </p>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RegisterForm;