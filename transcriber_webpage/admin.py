from django.contrib import admin
from .models import *
# Register your models here.

register_models = [Profile, ChatHistory]

admin.site.register(register_models)


