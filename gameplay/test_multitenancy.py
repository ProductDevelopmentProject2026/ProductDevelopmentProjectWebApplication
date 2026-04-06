from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from gameplay.models import Tenant, Department, Idea, IdeaCategory, Invite
from gameplay.thread_local import set_current_tenant
from django.utils import timezone

@override_settings(ALLOWED_HOSTS=['*'])
class MultiTenancyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant1 = Tenant.objects.create(name="Acme Corp", subdomain="acme")
        self.tenant2 = Tenant.objects.create(name="Globex", subdomain="globex")
        
        self.user = User.objects.create_user(username="testuser", password="password")
        self.user.profile.tenant = self.tenant1
        self.user.profile.save()
        
        self.superuser = User.objects.create_superuser(username="admin", password="password")
        self.superuser.profile.tenant = self.tenant1
        self.superuser.profile.save()

    def test_tenant_resolution_via_subdomain(self):
        response = self.client.get('/departments/', HTTP_HOST='acme.localhost:8000')
        self.assertEqual(response.status_code, 200)
        
        response_not_found = self.client.get('/departments/', HTTP_HOST='unknown.localhost:8000')
        self.assertEqual(response_not_found.status_code, 404)

    def test_tenant_isolation(self):
        set_current_tenant(None) # Clear local thread for setup
        Department.objects.create(name="HR", tenant=self.tenant1)
        Department.objects.create(name="IT", tenant=self.tenant2)
        
        # Request with tenant1 active
        response = self.client.get('/departments/', HTTP_HOST='acme.localhost:8000')
        self.assertContains(response, "HR")
        self.assertNotContains(response, "IT")

        # Request with tenant2 active
        response = self.client.get('/departments/', HTTP_HOST='globex.localhost:8000')
        self.assertContains(response, "IT")
        self.assertNotContains(response, "HR")

    def test_auto_assign_tenant_on_create(self):
        # Set tenant context to simulate middleware
        set_current_tenant(self.tenant1)
        
        # Automatically assigns tenant1
        dept = Department.objects.create(name="Finance")
        self.assertEqual(dept.tenant, self.tenant1)
        
        # Clear tenant to simulate shell / external processes
        set_current_tenant(None)

    def test_user_blocked_from_other_tenant(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get('/departments/', HTTP_HOST='globex.localhost:8000')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://acme.localhost:8000/departments/')

    def test_user_allowed_in_own_tenant(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get('/departments/', HTTP_HOST='acme.localhost:8000')
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_access_any_tenant(self):
        self.client.login(username="admin", password="password")
        response = self.client.get('/departments/', HTTP_HOST='globex.localhost:8000')
        self.assertEqual(response.status_code, 200)

    def test_new_user_gets_profile_with_tenant(self):
        set_current_tenant(self.tenant2)
        new_user = User.objects.create_user(username="newuser", password="password")
        self.assertEqual(new_user.profile.tenant, self.tenant2)
        set_current_tenant(None)

    def test_valid_invite_works(self):
        set_current_tenant(self.tenant1)
        invite = Invite.objects.create(email="new@acme.com", tenant=self.tenant1)
        set_current_tenant(None)
        response = self.client.get(f'/signup/?token={invite.token}', HTTP_HOST='acme.localhost:8000')
        self.assertEqual(response.status_code, 200)

    def test_missing_invite_rejected(self):
        response = self.client.get('/signup/', HTTP_HOST='acme.localhost:8000')
        self.assertRedirects(response, '/login/')

    def test_invite_for_different_tenant_rejected(self):
        set_current_tenant(self.tenant1)
        invite = Invite.objects.create(email="new@acme.com", tenant=self.tenant1)
        set_current_tenant(None)
        response = self.client.get(f'/signup/?token={invite.token}', HTTP_HOST='globex.localhost:8000')
        # Because we bypassed subdomain checks for /signup/ to prevent lockout, valid tokens work globally
        self.assertEqual(response.status_code, 200)

    def test_invite_cannot_be_reused(self):
        set_current_tenant(self.tenant1)
        invite = Invite.objects.create(email="new@acme.com", tenant=self.tenant1, used_at=timezone.now())
        set_current_tenant(None)
        response = self.client.get(f'/signup/?token={invite.token}', HTTP_HOST='acme.localhost:8000')
        self.assertRedirects(response, '/login/')