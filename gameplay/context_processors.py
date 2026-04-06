from .models import Tenant

def tenants_processor(request):
    return {
        'tenants': Tenant.objects.all(),
        'active_tenant': getattr(request, 'tenant', None)
    }