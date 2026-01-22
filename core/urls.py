from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView
from . import views
from . import admin_views

urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('dashboard'), permanent=False), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', admin_views.CustomAdminLogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('reports/', include('reports.urls')),
    path('customers/', include('customers.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('stock/', include('stock.urls')),
    path('sales/', include('sales.urls')),
    path('purchases/', include('purchases.urls')),
    path('expenses/', include('expenses.urls')),
    path('banking/', include('bankloan.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
