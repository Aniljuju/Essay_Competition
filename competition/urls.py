from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('competitions/', views.competition_list, name='competition_list'),
    path('competition/<int:competition_id>/write/', views.essay_write, name='essay_write'),
    path('essay/<int:essay_id>/', views.essay_view, name='essay_view'),
    path('competition/<int:competition_id>/leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Admin pages
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/essays/', views.admin_essays, name='admin_essays'),
]