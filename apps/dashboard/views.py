"""
Dashboard views - Role-based home pages.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone


@login_required
def dashboard_home(request):
    """
    Main dashboard view with role-based content.
    
    Displays different statistics and quick actions based on user's role.
    """
    context = {
        'page_title': 'Dashboard',
    }
    
    # Get user's role from profile
    try:
        role = request.user.profile.role
    except:
        role = None
    
    # Common stats for all roles
    context['user'] = request.user
    context['role'] = role
    
    # Role-specific data would be loaded here in future phases
    # For now, just render the base dashboard template
    
    return render(request, 'dashboard/home.html', context)
