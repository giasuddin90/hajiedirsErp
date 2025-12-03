from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.contrib import admin
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

class CustomAdminLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

class CustomAdminLogoutView(LogoutView):
    next_page = '/admin/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Log the user out
        logout(request)
        # Redirect to admin login page
        return HttpResponseRedirect(self.next_page)

# Override the admin login and logout views
admin.site.login = CustomAdminLoginView.as_view()
admin.site.logout = CustomAdminLogoutView.as_view()
