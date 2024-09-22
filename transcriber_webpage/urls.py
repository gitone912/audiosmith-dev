from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import RegisterView, home , profile


urlpatterns = [
    path("", views.index, name="index"),
    path("test", views.test, name="test"),
    path("api_key",views.get_api_key,name='apikey'),
    path('users', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),

]


# add at the last
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)