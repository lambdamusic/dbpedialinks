# Generated by Django 3.2.10 on 2021-12-20 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DBPediaEntity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=250, null=True, verbose_name='title')),
                ('uri', models.URLField(max_length=300)),
                ('totarticles', models.IntegerField(blank=True, null=True, verbose_name='Tot associated articles')),
                ('dbtype', models.CharField(blank=True, max_length=200, verbose_name='dbtype')),
                ('description', models.TextField(blank=True, verbose_name='description (put everything in here for now)')),
            ],
            options={
                'verbose_name': 'DBPedia Entity',
                'verbose_name_plural': 'DBPedia Entities',
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Subject_Rel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(null=True)),
                ('subject1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='is_subject_in_relations', to='dbpedialinks.dbpediaentity')),
                ('subject2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='is_object_in_relations', to='dbpedialinks.dbpediaentity')),
            ],
        ),
        migrations.CreateModel(
            name='SGDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=250, null=True, verbose_name='title')),
                ('uri', models.URLField(max_length=300)),
                ('author', models.CharField(blank=True, max_length=200, verbose_name='author')),
                ('pubyear', models.IntegerField(blank=True, null=True, verbose_name='publication year')),
                ('description', models.TextField(blank=True, verbose_name='description (put everything in here for now)')),
                ('dbentities', models.ManyToManyField(to='dbpedialinks.DBPediaEntity')),
            ],
            options={
                'verbose_name': 'SGDocument',
                'verbose_name_plural': 'SGDocuments',
                'ordering': ['uri'],
            },
        ),
        migrations.AddField(
            model_name='dbpediaentity',
            name='top_rel_subjects',
            field=models.ManyToManyField(through='dbpedialinks.Subject_Rel', to='dbpedialinks.DBPediaEntity'),
        ),
    ]
