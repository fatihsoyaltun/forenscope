from django.urls import path
from .views import UserListView, UserCreateView, UserEditView, ProfileView, CustomPasswordChangeView

app_name = 'accounts'

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/new/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserEditView.as_view(), name='user_edit'),
]
