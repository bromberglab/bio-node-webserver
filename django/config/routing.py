from django.conf.urls import url
from channels.http import AsgiHandler
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import django_eventstream

application = ProtocolTypeRouter({
    'http': URLRouter([
        url(r'^api/events/', AuthMiddlewareStack(
            URLRouter(django_eventstream.routing.urlpatterns)
        ), {'channels': ['event']}),
        url(r'', AsgiHandler),
    ]
    ),
})
