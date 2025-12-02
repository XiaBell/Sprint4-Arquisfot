"""
Middleware for RBAC Authorization
"""
import requests
import time
from django.conf import settings
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


def require_gestor_role(view_func):
    """
    Decorator que valida que el usuario tenga rol GESTOR
    Llama al Auth Service para validar el JWT y extraer el rol
    """
    def wrapper(request, *args, **kwargs):
        # Extraer token del header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'error': 'Missing or invalid Authorization header'
            }, status=401)
        
        token = auth_header.replace('Bearer ', '')
        
        # Medir tiempo de validación (para trade-off de seguridad)
        start_time = time.time()
        
        try:
            # Llamar al Auth Service para validar el token
            auth_service_url = f"{settings.AUTH_SERVICE_URL}/api/v1/auth/validate"
            response = requests.post(
                auth_service_url,
                json={'token': token},
                timeout=5
            )
            
            validation_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code != 200:
                logger.warning(f"Token validation failed: {response.status_code}")
                return JsonResponse({
                    'error': 'Invalid or expired token',
                    'validation_time_ms': round(validation_time, 2)
                }, status=401)
            
            auth_data = response.json()
            
            if not auth_data.get('isValid'):
                return JsonResponse({
                    'error': 'Invalid token',
                    'validation_time_ms': round(validation_time, 2)
                }, status=401)
            
            rol = auth_data.get('rol')
            user_id = auth_data.get('userId')
            
            # RBAC: Solo GESTOR puede modificar/eliminar ítems
            if rol != 'GESTOR':
                logger.warning(f"Access denied for role: {rol}")
                return JsonResponse({
                    'error': 'Forbidden: Only GESTOR role can perform this action',
                    'rol': rol,
                    'validation_time_ms': round(validation_time, 2)
                }, status=403)
            
            # Agregar información del usuario al request
            request.user_id = user_id
            request.user_rol = rol
            request.validation_time_ms = validation_time
            
            # Continuar con la vista
            return view_func(request, *args, **kwargs)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling auth service: {e}")
            return JsonResponse({
                'error': 'Auth service unavailable',
                'validation_time_ms': (time.time() - start_time) * 1000
            }, status=503)
        except Exception as e:
            logger.error(f"Unexpected error in RBAC middleware: {e}")
            return JsonResponse({
                'error': 'Internal server error'
            }, status=500)
    
    return wrapper


def optional_auth(view_func):
    """
    Decorator opcional que extrae información del usuario si está autenticado
    pero no requiere un rol específico
    """
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            
            try:
                auth_service_url = f"{settings.AUTH_SERVICE_URL}/api/v1/auth/validate"
                response = requests.post(
                    auth_service_url,
                    json={'token': token},
                    timeout=5
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    if auth_data.get('isValid'):
                        request.user_id = auth_data.get('userId')
                        request.user_rol = auth_data.get('rol')
            except Exception as e:
                logger.warning(f"Optional auth failed: {e}")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

