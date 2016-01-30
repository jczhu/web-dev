import os
import sys
import urllib2
import re
import logging

from xml.dom import minidom
from string import letters

import jinja2
import webapp2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

IP_URL = "http://ip-api.com/xml/?="
def get_coords(ip):
	
	url = IP_URL + ip
	content = None
	try:
		content = urllib2.urlopen(url).read()
	except urllib2.URLError:
		return

	if content:
		#parse the xml and find the coordinates
		d = minidom.parseString(content)
		status = d.getElementsByTagName('status')[0].childNodes[0].nodeValue
		if status == 'success':
			lonNode = d.getElementsByTagName('lon')[0]
			latNode = d.getElementsByTagName('lat')[0]
			if lonNode and latNode and lonNode.childNodes[0].nodeValue and latNode.childNodes[0].nodeValue:
				lon = lonNode.childNodes[0].nodeValue
				lat = latNode.childNodes[0].nodeValue
				return db.GeoPt(lat, lon)

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
def gmaps_img(points):
	markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)
	return GMAPS_URL + markers

class Art(db.Model):
	title = db.StringProperty(required = True)
	art = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	coords = db.GeoPtProperty() #not required because would affect old art submissions

CACHE = {}
def top_arts(update=False):
	key = 'top'
	if not update and key in CACHE:
		arts = CACHE[key]
	else:
		logging.error("DB QUERY")
		arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")
		arts = list(arts) #arts was cursor, prevent multiple queries
		CACHE[key] = arts
	return arts

class MainPage(Handler):
	def render_front(self, title="", art="", error=""):
		arts = top_arts()
		
		#find which arts have coords
		points = filter(None, (a.coords for a in arts)) #return art coords that aren't none
		
		#if we have any arts coords, make image url
		img_url = None
		if points:
			img_url = gmaps_img(points)
		
		
		#display image url
		self.render("front.html", title=title, art=art, error=error, arts = arts,
			img_url=img_url)

	def get(self):
		return self.render_front()

	def post(self):
		title = self.request.get("title")
		art = self.request.get("art")

		if title and art:
			a = Art(title = title, art = art)
			#if we have coords, add to Art object
			coords = get_coords(self.request.remote_addr)
			if coords:
				a.coords = coords

			a.put()
			#rerun the query and update the cache
			top_arts(True)

			self.redirect("/")
		else:
			error = "we need both a title and some artwork"
			self.render_front(title, art, error)

app = webapp2.WSGIApplication([
	('/', MainPage)
], debug=True)