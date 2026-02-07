from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tables/', views.TableListView.as_view(), name='table_list'),
    path('tables/create/', views.TableCreateView.as_view(), name='table_create'),
    path('tables/<int:pk>/edit/', views.TableUpdateView.as_view(), name='table_edit'),
    path('tables/<int:pk>/delete/', views.TableDeleteView.as_view(), name='table_delete'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('currency-converter/', views.currency_converter, name='currency_converter'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]