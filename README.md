# DBpedia links project

Navigation of the links to DBpedia generated in the context of https://github.com/dbpedia/sci-graph-links


## Tech info

This is a Django app which is mirrored in local using `wget` and rendered as a static site in /docs.

To experience all the app functionalities, it should be run using Django and a web server. 

The `docs` folder contains a static version of the site, which is accessible at: 

* http://dbpedialinks.michelepasin.org/


## Static export limits

NOTE in order to keep the exported site size manageable, only a subset of DBpedia subjects have been used.

To this end, a filter in `models.py` removes subjects that have less that 10 associated articles:

```python

class FilteredModelManager(models.Manager):
    """A custom model manager that filters out DBPediaEntity subjects with less than 2 articles.
    This ensures that we never generate too many pages when building a static dump of the site"""
    def get_queryset(self):
        if DEMO_MODE_FLAG:
            return super(MyModelManager, self).get_queryset().filter(totarticles__gt=10)
        else:
            return super(MyModelManager, self).get_queryset()

```

This results in ~7k subjects, instead of the ~50k in the dataset.


## Recreating the dataset 

Unzip the file in `backups/dbpedialinks.zip` and load it into the DB. 

```
src/manage.py loaddata backups/dbpedialinks.json
```

NOTE The Django DB should already be initialised before doing this. IE

```
src/manage.py makemigrations
src/manage.py migrate
```

Remember to set `local_settings.DEMO_MODE_FLAG` to false in order to see all subjects. 


## Status

This project is here for documentation purposes and is no longer under development.