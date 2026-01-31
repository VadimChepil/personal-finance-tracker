from django.views.generic import CreateView, FormView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import SignUpForm, SignInForm


class SignUpView(CreateView):
    form_class = SignUpForm 
    template_name = 'authentication/registration.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class SignInView(FormView):
    form_class = SignInForm
    template_name = 'authentication/login.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')