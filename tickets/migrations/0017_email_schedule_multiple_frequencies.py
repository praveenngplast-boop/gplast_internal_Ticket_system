import json

from django.db import migrations, models


VALID_FREQUENCIES = {'daily', 'weekly', 'monthly'}


def convert_frequency_to_list(apps, schema_editor):
    EmailSchedule = apps.get_model('tickets', 'EmailSchedule')
    table_name = schema_editor.quote_name(EmailSchedule._meta.db_table)
    for schedule in EmailSchedule.objects.all():
        frequency = schedule.frequency
        if isinstance(frequency, str):
            frequencies = [frequency] if frequency in VALID_FREQUENCIES else ['daily']
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE {table_name} SET frequency = %s WHERE id = %s',
                    [json.dumps(frequencies), schedule.pk],
                )


def convert_frequency_to_string(apps, schema_editor):
    EmailSchedule = apps.get_model('tickets', 'EmailSchedule')
    table_name = schema_editor.quote_name(EmailSchedule._meta.db_table)
    for schedule in EmailSchedule.objects.all():
        frequencies = schedule.frequency if isinstance(schedule.frequency, list) else [schedule.frequency]
        frequency = next((frequency for frequency in frequencies if frequency in VALID_FREQUENCIES), 'daily')
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE {table_name} SET frequency = %s WHERE id = %s',
                [frequency, schedule.pk],
            )


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0016_emailschedule_unithead'),
    ]

    operations = [
        migrations.RunPython(convert_frequency_to_list, convert_frequency_to_string),
        migrations.AlterField(
            model_name='emailschedule',
            name='frequency',
            field=models.JSONField(default=list),
        ),
    ]
