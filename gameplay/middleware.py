from django.http import Http404
from django.shortcuts import redirect
from .models import Tenant
from .thread_local import set_current_tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass tenant resolution and checks for admin, auth, and static/media routes
        if request.path.startswith(('/admin/', '/login/', '/logout/', '/static/', '/media/', '/signup/', '/register/')):
            request.tenant = None
            set_current_tenant(None)
            return self.get_response(request)

        tenant = None

        # 1) Querystring: ?tenant=hoptrans
        tenant_slug = request.GET.get('tenant')
        if tenant_slug:
            tenant = Tenant.objects.filter(subdomain=tenant_slug).first()
            if not tenant:
                raise Http404("Organization not found.")

        # 2) Subdomain fallback
        if not tenant:
            host = request.get_host().split(':')[0]
            is_ip = all(part.isdigit() for part in host.split('.'))
            subdomain = host.split('.')[0]
            
            # Added testserver to prevent Django's default test client from triggering a 404
            # Skip subdomain checks for IP addresses
            if subdomain and not is_ip and subdomain not in ['www', 'localhost', 'testserver']:
                tenant = Tenant.objects.filter(subdomain=subdomain).first()
                if not tenant:
                    raise Http404("Organization not found.")

        # 3) Default fallback
        if not tenant:
            tenant = Tenant.objects.filter(subdomain='default').first()
            if not tenant:
                # If the 'default' tenant was renamed or deleted, safely fallback to the first available
                tenant = Tenant.objects.first()
            
            if not tenant:
                # Provide a default tenant in test DB setup or fresh installations
                tenant, _ = Tenant.objects.get_or_create(
                    subdomain='default',
                    defaults={'name': 'Default Organization'}
                )

        # 4) Enforce strict user-tenant isolation (superusers bypass this)
        if tenant and hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_superuser:
            if hasattr(request.user, 'profile') and request.user.profile.tenant_id != tenant.id:
                user_tenant = request.user.profile.tenant
                if user_tenant and user_tenant.subdomain:
                    current_host = request.get_host()
                    if current_host.startswith('www.'):
                        current_host = current_host[4:]

                    # Handle IP address (localhost/cloud IP) properly, use querystring instead of subdomain
                    is_current_ip = all(part.isdigit() for part in current_host.split(':')[0].split('.'))
                    if is_current_ip or current_host.startswith('localhost') or current_host.startswith('testserver'):
                        # Keep existing query params and add/update tenant
                        query_dict = request.GET.copy()
                        query_dict['tenant'] = user_tenant.subdomain
                        return redirect(f"{request.scheme}://{current_host}{request.path}?{query_dict.urlencode()}")

                    if tenant.subdomain and current_host.startswith(tenant.subdomain + '.'):
                        new_host = current_host.replace(tenant.subdomain + '.', user_tenant.subdomain + '.', 1)
                    else:
                        new_host = f"{user_tenant.subdomain}.{current_host}"

                    return redirect(f"{request.scheme}://{new_host}{request.get_full_path()}")
                else:
                    raise Http404("Organization not found.")

        request.tenant = tenant
        set_current_tenant(tenant)

        try:
            response = self.get_response(request)
        finally:
            set_current_tenant(None)

        return response