from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static
from . import consumers

websocket_urlpatterns = [
   re_path(r"listen", consumers.TranscriptConsumer.as_asgi()),
]

# # add at the last
# websocket_urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
# websocket_urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)