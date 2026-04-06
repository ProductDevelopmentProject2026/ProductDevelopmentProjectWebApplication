from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Tenant, Department, Profile, ActionLog, IdeaCategory, Idea, Training, Question, QuizResult, Lesson, TrainingFeedback, Problem, TenantAwareModel, Invite

class TenantAwareAdmin(admin.ModelAdmin):
    exclude = ('tenant',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(tenant=request.tenant)
        if request.user.is_superuser and not getattr(request, 'tenant', None):
            return qs # Fallback: allow superusers to see everything if no tenant is active
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'tenant_id', None) and hasattr(request, 'tenant') and request.tenant:
            obj.tenant = request.tenant
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if hasattr(request, 'tenant') and request.tenant:
            if issubclass(db_field.related_model, TenantAwareModel):
                kwargs["queryset"] = db_field.related_model.objects.filter(tenant=request.tenant)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ProfileAdmin(TenantAwareAdmin):
    exclude = () # Ensure the tenant field is visible for profiles

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

class InviteAdmin(TenantAwareAdmin):
    exclude = () # Ensure the tenant field is visible for invites
    list_display = ('email', 'tenant', 'token', 'used_at', 'created_at')
    list_filter = ('tenant', 'used_at', 'created_at')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Tenant)
admin.site.register(Department, TenantAwareAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ActionLog, TenantAwareAdmin)
admin.site.register(IdeaCategory, TenantAwareAdmin)
admin.site.register(Idea, TenantAwareAdmin)
admin.site.register(Training, TenantAwareAdmin)
admin.site.register(Question, TenantAwareAdmin)
admin.site.register(QuizResult, TenantAwareAdmin)
admin.site.register(Lesson, TenantAwareAdmin)
admin.site.register(TrainingFeedback, TenantAwareAdmin)
admin.site.register(Problem, TenantAwareAdmin)
admin.site.register(Invite, InviteAdmin)