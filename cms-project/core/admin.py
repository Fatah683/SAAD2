"""
Django Admin configuration for the Complaint Management System.

Provides admin interfaces for:
- Tenant management
- User/UserProfile management
- Complaint inspection
- Audit log viewing
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Tenant, UserProfile, Complaint, AuditLog


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile within User admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline."""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_tenant', 'get_role', 'is_staff')
    list_filter = BaseUserAdmin.list_filter + ('profile__tenant', 'profile__role')

    def get_tenant(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.tenant.name
        return '-'
    get_tenant.short_description = 'Tenant'
    get_tenant.admin_order_field = 'profile__tenant__name'

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant management."""
    list_display = ('name', 'slug', 'is_active', 'created_at', 'user_count', 'complaint_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Users'

    def complaint_count(self, obj):
        return obj.complaints.count()
    complaint_count.short_description = 'Complaints'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile management."""
    list_display = ('user', 'tenant', 'role', 'phone', 'created_at')
    list_filter = ('tenant', 'role', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    raw_id_fields = ('user',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """Admin interface for Complaint inspection."""
    list_display = ('reference_number', 'title', 'tenant', 'status', 'priority', 
                    'submitted_by', 'assigned_to', 'created_at')
    list_filter = ('tenant', 'status', 'priority', 'created_at')
    search_fields = ('reference_number', 'title', 'description')
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'resolved_at', 'closed_at')
    raw_id_fields = ('submitted_by', 'logged_by', 'assigned_to')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('reference_number', 'tenant', 'title', 'description', 'category')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('People', {
            'fields': ('submitted_by', 'logged_by', 'assigned_to')
        }),
        ('Resolution', {
            'fields': ('resolution_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for viewing audit logs (read-only)."""
    list_display = ('complaint', 'action', 'user', 'old_value', 'new_value', 'created_at')
    list_filter = ('tenant', 'action', 'created_at')
    search_fields = ('complaint__reference_number', 'details')
    readonly_fields = ('tenant', 'complaint', 'user', 'action', 'details', 
                       'old_value', 'new_value', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.site_header = 'Complaint Management System'
admin.site.site_title = 'CMS Admin'
admin.site.index_title = 'Administration'
