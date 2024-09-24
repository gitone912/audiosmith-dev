from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import RegisterView, home , profile


urlpatterns = [
    path("", views.index, name="new_entry"),
    path('all_entries', views.all_journal_entries, name='all_entries'),
    path("test", views.test, name="test"),
    path("api_key",views.get_api_key,name='apikey'),
    path('users', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('create_journal_entry', views.create_journal_entry, name='create_journal_entry'),
     path('edit_entry/<int:entry_id>/', views.edit_journal_entry, name='edit_entry'),

]


# add at the last
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)