from django.db import migrations

def backfill_tenant_data(apps, schema_editor):
    # Get the historical version of the models
    Tenant = apps.get_model('gameplay', 'Tenant')
    
    # 1. Create a default Tenant if it doesn't exist
    default_tenant, created = Tenant.objects.get_or_create(
        subdomain="default",
        defaults={"name": "Default"}
    )

    # 2. List of all models that now have a tenant_id
    tenant_models = [
        'Department',
        'Profile',
        'ActionLog',
        'IdeaCategory',
        'Idea',
        'Training',
        'Question',
        'QuizResult',
        'Lesson',
        'TrainingFeedback',
        'Problem'
    ]

    # 3. Update all existing records where tenant is NULL
    for model_name in tenant_models:
        Model = apps.get_model('gameplay', model_name)
        Model.objects.filter(tenant__isnull=True).update(tenant=default_tenant)

def reverse_backfill(apps, schema_editor):
    # Optional: logic to reverse the migration if you ever need to rollback.
    # In this case, doing nothing is usually safe since dropping the columns 
    # in the previous migration handles the rollback automatically.
    pass

class Migration(migrations.Migration):

    dependencies = [
    ('gameplay', '0017_tenant_actionlog_tenant_department_tenant_and_more'),
]

    operations = [
        migrations.RunPython(backfill_tenant_data, reverse_code=reverse_backfill),
    ]
