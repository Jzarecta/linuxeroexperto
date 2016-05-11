#!/bin/env python
import sys
import os
import math
import random
import datetime

from models import *
import defs
import request

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util



class AbstractPageHandler(request.BlogRequestHandler):
    def get_tag_counts(self):
	tag_counts = Article.get_all_tags()
	result = []
	if tag_counts:
	    maximum = max(tag_counts.values())

	    for tag, count in tag_counts.items():
		tc = TagCount(tag, count)

		percent = math.floor((tc.count * 100) / maximum)

		if percent <= 20:
		    tc.css_class = 'tag-cloud-tiny'
		elif 20 < percent <= 40:
		    tc.css_class = 'tag-cloud-small'
		elif 40 < percent <= 60:
		    tc.css_class <= 'tag-cloud-medium'
		elif 60 < percent <= 80:
		    tc.css_class = 'tag-cloud-large'
		else:
		    tc.css_class = 'tag-cloud-huge'

		result.append(tc)

	random.shuffle(result)
	return result

    def get_month_counts(self):
	hash = Article.get_all_datetimes()
	datetimes = hash.keys()
	date_count = {}
	for dt in datetimes:
	    just_date = datetime.date(dt.year, dt.month, 1)
	    try:
		date_count[just_date] += hash[dt]
	    except KeyError:
		date_count[just_date] = hash[dt]

        dates = date_count.keys()
	dates.sort()
	dates.reverse()
	return [DateCount(date, date_count[date]) for date in dates]

    def render_articles(self,
	                articles,
			request,
			recent,
			template_name='show-articles.html'):
	url_prefix = 'http://' + request.environ['SERVER_NAME']
        port = request.environ['SERVER_PORT']
	if port:
	    url_prefix += ':%s' % port
	
	self.augment_articles(articles, url_prefix)
	self.augment_articles(recent, url_prefix)

	last_updated = datetime.datetime.now()
	if articles:
	    last_update = articles[0].published_when

	#self.adjust_timestamp(articles)
	#last_updated = self.adjust_timestamp(last_updated)

	blog_url = url_prefix
	tag_path = '/' +  defs.TAG_URL_PATH
	tag_url = url_prefix + tag_path
	date_path = '/' + defs.DATE_URL_PATH
	date_url = url_prefix + date_path
	media_path = '/' + defs.MEDIA_URL_PATH
	media_url = url_prefix + media_path

	template_variables = {'blog_name'   : defs.BLOG_NAME,
		              'blog_owner'  : defs.BLOG_OWNER,
			      'articles'    : articles,
			      'tag_list'    : self.get_tag_counts(),
			      'date_list'   : self.get_month_counts(),
			      'version'     : '0.3',
			      'last_updated': last_updated,
			      'blog_path'   : '/',
			      'blog_url'    : blog_url,
			      'archive_path': '/' + defs.ARCHIVE_URL_PATH,
			      'tag_path'    : tag_path,
			      'tag_url'     : tag_url,
			      'date_path'   : date_path,
			      'date_url'    : date_url,
			      'atom_path'   : '/' + defs.ATOM_URL_PATH,
			      'rss2_path'   : '/' + defs.RSS2_URL_PATH,
			      'media_path'  : media_path,
			      'recent'      : recent}

	return self.render_template(template_name, template_variables)

    def get_recent(self):
	articles = Article.published()

	total_recent = min(len(articles), defs.TOTAL_RECENT)
	if articles:
	    recent = articles[0:total_recent]
	else:
	    recent = []
	
	return recent

    def augment_articles(self, articles, url_prefix, html=True):
	for article in articles:
	    if html:
		try:
		    article.html = article.body
		except AttributeError:
		    article.html = ''
	    article.path = '/' + defs.ARTICLE_URL_PATH + '/%s' % article.id
	    article.url = url_prefix + article.path


class FrontPageHandler(AbstractPageHandler):
    def get(self):
	articles = Article.published()
	if len(articles) > defs.MAX_ARTICLES_PER_PAGE:
	    articles = articles[:defs.MAX_ARTICLES_PER_PAGE]

	self.response.out.write(self.render_articles(articles,
	    					     self.request,
						     self.get_recent()))

class ArchivePageHandler(AbstractPageHandler):
    def get(self):
	articles = Article.published()
	self.response.out.write(self.render_articles(articles,
	   					     self.request,
						     [],
						     'archive.html'))

class SingleArticleHandler(AbstractPageHandler):
    def get(self, id):
        article = Article.get(int(id))
	if article:
	    template = 'show-articles.html'
	    articles = [article]
	    more = None
	else:
	    template = 'not-found.html'
	    articles = []

	self.response.out.write(self.render_articles(articles=articles,
	                                             request=self.request,
						     recent=self.get_recent(),
						     template_name=template))

application = webapp.WSGIApplication(
	      [('/', FrontPageHandler),
	    #   ('/tag/([^/]+)/*$', ArticlesByTagHandler),
	    #   ('/date/(\d\d\d\d)-(\d\d)/?$', ArticlesForMonthHandler),
	       ('/id/(\d+)/?$', SingleArticleHandler),
	       ('/archive/?$', ArchivePageHandler),
	    #   ('/rss2/?$', RSSFeedHandler),
	    #   ('/atom/?$', AtomFeedHandler),
	    #   ('/.*$', NotFoundPageHandler),
	      ],
              
	      debug=True)
def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
