from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Pages
    path('',                       views.dashboard,          name='dashboard'),
    path('users/',                 views.users,              name='users'),
    path('essays/',                views.essays,             name='essays'),
    path('competitions/create/',   views.create_competition, name='create_competition'),

    # AJAX endpoints
    path('ajax/user/status/',      views.update_user_status, name='update_user_status'),
    path('ajax/user/delete/',      views.delete_user,        name='delete_user'),
    path('ajax/essay/action/',     views.essay_action,       name='essay_action'),
    path('ajax/essay/<int:essay_id>/detail/', views.essay_detail, name='essay_detail'),
]
