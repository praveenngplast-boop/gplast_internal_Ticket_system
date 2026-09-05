from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0002_ticket_target_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_name', models.CharField(max_length=150)),
                ('author_role', models.CharField(max_length=30)),
                ('body', models.TextField()),
                ('attachment', models.FileField(blank=True, null=True, upload_to='attachments/replies/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='tickets.ticket')),
            ],
            options={'ordering': ['created_at']},
        ),
    ]