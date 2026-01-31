from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from users.views import SignUpView, SignInView, CustomLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home/index.html'), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]
