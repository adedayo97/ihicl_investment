from django.contrib import admin
from django.urls import path,include
from ihicl_main import views  # This imports all views from ihicl_main
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('investments/', views.investments, name='investments'),
    path('partners/', views.projects, name='partners'),
    path('faqs/', views.faqs, name='faqs'),
    path('roadmap/', views.roadmap_view, name='roadmap'),
    path('contact/', views.contact_view, name='contact'),
    path('search/', views.search, name='search'),  # Access search through views
    #path('invest/login/', views.investment_login, name='investment_login'),
    path('invest/register/', views.investment_register, name='investment_register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/', include('django.contrib.auth.urls')),


    # Custom authentication views that redirect to Django's auth system
    path('investor/login/', views.investment_login, name='investment_login'),
    path('invest/register/', views.investment_register, name='investment_register'),
    path('map/', views.map_view, name='map'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-next-of-kin/', views.update_next_of_kin, name='update_next_of_kin'),
    path('invest-form/', views.invest_form, name='invest_form'),
    path('withdraw/', views.withdraw_form, name='withdraw_form'),
    path('statement-request/', views.statement_request, name='statement_request'),
    path('cleanup-duplicates/', views.cleanup_duplicates, name='cleanup_duplicates'),
    # Add this to urls.py (assuming you have a urls.py file)
# from .views import withdraw_form

    

]

# This is IMPORTANT for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)