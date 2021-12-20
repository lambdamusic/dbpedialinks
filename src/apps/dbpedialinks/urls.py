from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

app_name = 'dbpedialinks'
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^entities$', views.entities, name='entities'),
    url(r'^entities/(?P<entity_id>\d+)$',
        views.entities,
        name='entities_detail'),
    url(r'^graph_test/(?P<entity_id>\d+)$',
        views.graph_test,
        name='graph_test'),
    url(r'^graph_test_two_levels/(?P<entity_id>\d+)$',
        views.graph_test_two_levels,
        name='graph_test_two_levels'),
    url(r'^ajax/sg$', views.ajax_scigraph, name='ajax_scigraph'),
    url(r'^ajax/tags$', views.ajax_tags_info, name='ajax_tags_info'),
    url(r'^ajax/dbpedia$', views.ajax_dbpedia_info, name='ajax_dbpedia_info'),

    # not used:
    url(r'^articles$', views.articles, name='articles'),
    # url(r'^articles/(?P<article_id>\d+)$',
    # views.articles,
    # name='articles_detail'),
]
