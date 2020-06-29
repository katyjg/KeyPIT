"""keypit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from keypit.kpis.views import LandingPage

urlpatterns = [
    url(r'^$', login_required(LandingPage.as_view()), {}, 'landing'),
    path('admin/', admin.site.urls),
    path('keypit/',  include('keypit.kpis.urls')),
]

if settings.CAS_ENABLED:
    from django_cas_ng import views as casviews

    urlpatterns += [
        path('accounts/login/', casviews.LoginView.as_view(), name='login'),
        path('accounts/logout/', casviews.LogoutView.as_view(), name='logout'),
        path('accounts/callback/', casviews.CallbackView.as_view(), name='cas_ng_proxy_callback'),

    ]
else:
    urlpatterns += [
        path('accounts/login/', LoginView.as_view(template_name='login.html'), name="login"),
        path('accounts/logout/', LogoutView.as_view(), name="logout"),
    ]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

