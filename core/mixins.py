from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin):
    """Any authenticated user can access."""
    pass


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only superusers (admin) can access."""
    def test_func(self):
        return self.request.user.is_superuser


def admin_required(view_func):
    """Decorator for function-based views: only superusers allowed."""
    from django.contrib.auth.decorators import user_passes_test
    decorated = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated
