from django.db import migrations

def backfill_invite_tenant(apps, schema_editor):
    Invite = apps.get_model('gameplay', 'Invite')
    Tenant = apps.get_model('gameplay', 'Tenant')
    
    # Find the default or first available tenant
    default_tenant = Tenant.objects.filter(subdomain='default').first()
    if not default_tenant:
        default_tenant = Tenant.objects.first()
        
    # Safely backfill any orphaned invites
    if default_tenant:
        Invite.objects.filter(tenant__isnull=True).update(tenant=default_tenant)

class Migration(migrations.Migration):

    dependencies = [
        ('gameplay', '0018_backfill_tenant'),
    ]

    operations = [
        migrations.RunPython(backfill_invite_tenant),
    ]