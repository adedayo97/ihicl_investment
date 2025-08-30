from django.contrib import admin
from .models import (InvestmentSector, InvestmentOpportunity, TeamMember, Testimonial, FAQ, ContactSubmission, InvestorProfile,
    Investment, Transaction, NextOfKin)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.urls import reverse
from django.utils.html import format_html


class InvestmentOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'sector', 'investment_amount', 'is_featured')
    list_filter = ('sector', 'is_featured')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'order')
    list_editable = ('order',)


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_joined', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    readonly_fields = ('date_joined', 'last_login')

# Admin for InvestorProfile
# admin.py - Update InvestorProfileAdmin
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_title', 'telephone', 'country', 'city', 'created_at')
    list_filter = ('country', 'city', 'created_at', 'title')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'telephone')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_title(self, obj):
        return obj.get_full_title()
    get_title.short_description = 'Title'
    
    # Add user information to the detail view
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'title', 'other_title')
        }),
        ('Contact Information', {
            'fields': ('telephone', 'address', 'country', 'city', 'state', 'postal_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
# Admin for Investment
# admin.py - InvestmentAdmin
# admin.py - Use this updated InvestmentAdmin class


class InvestorFilter(SimpleListFilter):
    title = 'Investor'
    parameter_name = 'investor'

    def lookups(self, request, model_admin):
        # Get distinct investors who have investments
        investors = User.objects.filter(
            investments__isnull=False
        ).distinct().order_by('first_name', 'last_name', 'username')
        
        return [(investor.id, f"{investor.first_name} {investor.last_name}".strip() or investor.username) 
                for investor in investors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(investor__id=self.value())
        return queryset

class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('get_investor_name', 'get_investor_email', 'get_investment_type', 'amount', 'current_value', 'get_roi_percentage', 'status', 'date_invested')
    list_filter = (InvestorFilter, 'status', 'date_invested')
    search_fields = ('investor__username', 'investor__email', 'investor__first_name', 'investor__last_name', 'project__title')
    readonly_fields = ('date_invested', 'get_roi_percentage')
    list_select_related = ('investor',)  # Optimize database queries
    actions = ['mark_as_active', 'mark_as_completed', 'mark_as_pending', 'mark_as_cancelled']
    
    def get_investor_name(self, obj):
        investor_name = f"{obj.investor.first_name} {obj.investor.last_name}".strip() or obj.investor.username
        url = f"{reverse('admin:ihicl_main_investment_changelist')}?investor__id__exact={obj.investor.id}"
        return format_html('<a href="{}" title="View all investments for this investor">{}</a>', url, investor_name)
    get_investor_name.short_description = 'Investor Name'
    get_investor_name.admin_order_field = 'investor__last_name'
    
    def get_investor_email(self, obj):
        return obj.investor.email
    get_investor_email.short_description = 'Email'
    get_investor_email.admin_order_field = 'investor__email'
    
    def get_investment_type(self, obj):
        return obj.investment_type
    get_investment_type.short_description = 'Investment Type'
    
    def get_roi_percentage(self, obj):
        try:
            return f"{obj.roi_percentage:.2f}%"
        except (TypeError, ValueError, AttributeError):
            return "0.00%"
    get_roi_percentage.short_description = 'ROI %'
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = "Mark selected investments as Active"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected investments as Completed"
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_as_pending.short_description = "Mark selected investments as Pending"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = "Mark selected investments as Cancelled"


# admin.py - Updated TransactionAdmin class
class UserFilter(SimpleListFilter):
    title = 'User'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        # Get distinct users who have transactions
        users = User.objects.filter(
            transactions__isnull=False
        ).distinct().order_by('first_name', 'last_name', 'username')
        
        return [(user.id, f"{user.first_name} {user.last_name}".strip() or user.username) 
                for user in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__id=self.value())
        return queryset

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'get_user_email', 'transaction_type', 'amount', 'description', 'date', 'reference', 'status')
    list_filter = (UserFilter, 'transaction_type', 'status', 'date')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'reference', 'description')
    readonly_fields = ('date',)
    list_select_related = ('user',)  # Optimize database queries
    actions = ['mark_as_pending', 'mark_as_completed', 'mark_as_cancelled']
    
    def get_user_name(self, obj):
        user_name = f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        url = f"{reverse('admin:ihicl_main_transaction_changelist')}?user__id__exact={obj.user.id}"
        return format_html('<a href="{}" title="View all transactions for this user">{}</a>', url, user_name)
    get_user_name.short_description = 'User Name'
    get_user_name.admin_order_field = 'user__last_name'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_as_pending.short_description = "Mark selected transactions as Pending"
    
    def mark_as_completed(self, request, queryset):
        for transaction in queryset:
            transaction.status = 'completed'
            transaction.save()  # Triggers the save method to deduct from investments
    mark_as_completed.short_description = "Mark selected transactions as Completed"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = "Mark selected transactions as Cancelled"

# Admin for NextOfKin
class NextOfKinAdmin(admin.ModelAdmin):
    list_display = ('investor', 'full_name', 'relationship', 'email', 'phone')
    list_filter = ('relationship',)
    search_fields = ('investor__user__username', 'full_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')

# Admin for ContactSubmission
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('submitted_at',)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register all models
admin.site.register(InvestmentSector)
admin.site.register(InvestmentOpportunity)
admin.site.register(TeamMember)
admin.site.register(Testimonial)
admin.site.register(FAQ)
admin.site.register(ContactSubmission, ContactSubmissionAdmin)
admin.site.register(InvestorProfile, InvestorProfileAdmin)
admin.site.register(Investment, InvestmentAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(NextOfKin, NextOfKinAdmin)

# Optional: Create an admin dashboard
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = _('IHICL Investment Administration')
    site_title = _('IHICL Admin Portal')
    index_title = _('Welcome to IHICL Investment Admin')
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        context['index_title'] = self.index_title
        return context