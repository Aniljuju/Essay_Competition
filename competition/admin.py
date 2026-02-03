from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Competition, Essay, Paragraph

class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['status']


class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with profile inline
    """
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_status', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__status']
    
    def get_status(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.status
        return 'No Profile'
    get_status.short_description = 'Status'


class ParagraphInline(admin.TabularInline):
    """
    Inline admin for Paragraphs
    """
    model = Paragraph
    extra = 0
    readonly_fields = ['order', 'content', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    """
    Admin interface for Competition
    """
    list_display = ['title', 'start_date', 'end_date', 'max_paragraphs', 'is_active']
    list_filter = ['start_date', 'end_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    """
    Admin interface for Essay
    """
    list_display = ['user', 'competition', 'status', 'paragraph_count', 'word_count', 'started_at', 'completed_at']
    list_filter = ['status', 'competition', 'started_at']
    search_fields = ['user__username', 'competition__title']
    readonly_fields = ['started_at', 'completed_at', 'word_count']
    inlines = [ParagraphInline]
    date_hierarchy = 'started_at'
    
    def paragraph_count(self, obj):
        return obj.current_paragraph_count()
    paragraph_count.short_description = 'Paragraphs'
    
    actions = ['lock_essays', 'unlock_essays']
    
    def lock_essays(self, request, queryset):
        updated = queryset.update(status='locked')
        self.message_user(request, f'{updated} essays were locked.')
    lock_essays.short_description = 'Lock selected essays'
    
    def unlock_essays(self, request, queryset):
        updated = queryset.filter(status='locked').update(status='completed')
        self.message_user(request, f'{updated} essays were unlocked.')
    unlock_essays.short_description = 'Unlock selected essays'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile
    """
    list_display = ['user', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'


# Unregister the default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)