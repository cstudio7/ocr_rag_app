"""
Authentication and authorization decorators for role-based access control.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required

def permission_required(permission):
    """
    Decorator to require a specific permission for a route.
    
    Args:
        permission (str): The permission required ('search', 'upload', 'manage', 'user_management')
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                if request.is_json:
                    return jsonify({
                        'error': f'Access denied. Required permission: {permission}',
                        'required_permission': permission,
                        'user_role': current_user.role
                    }), 403
                else:
                    flash(f'Access denied. You need {permission} permission to access this page.', 'error')
                    return redirect(url_for('search'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(*roles):
    """
    Decorator to require specific roles for a route.
    
    Args:
        *roles: Variable number of role names that are allowed
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                if request.is_json:
                    return jsonify({
                        'error': f'Access denied. Required roles: {", ".join(roles)}',
                        'required_roles': list(roles),
                        'user_role': current_user.role
                    }), 403
                else:
                    flash(f'Access denied. Required roles: {", ".join(roles)}', 'error')
                    return redirect(url_for('search'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator 
def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin and current_user.role != 'admin':
            if request.is_json:
                return jsonify({
                    'error': 'Admin access required',
                    'user_role': current_user.role
                }), 403
            else:
                flash('Admin access required.', 'error')
                return redirect(url_for('search'))
        return f(*args, **kwargs)
    return decorated_function

def upload_required(f):
    """Decorator to require upload permission for a route."""
    return permission_required('upload')(f)

def manage_required(f):
    """Decorator to require manage permission for a route."""
    return permission_required('manage')(f)

def search_required(f):
    """Decorator to require search permission for a route."""
    return permission_required('search')(f)
