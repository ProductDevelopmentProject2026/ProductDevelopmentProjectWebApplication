from .models import Tenant, ActionLog

def tenants_processor(request):
    alert_count = 0
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request, 'tenant') and request.tenant:
        alert_count = ActionLog.objects.filter(tenant=request.tenant, user=request.user, is_read=False).count()
    
    return {
        'tenants': Tenant.objects.all(),
        'active_tenant': getattr(request, 'tenant', None),
        'alert_count': alert_count,
    }