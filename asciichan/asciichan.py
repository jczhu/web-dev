import os
import sys
import urllib2
import re

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
	ip = "4.2.2.2" # for testing (so won't get localhost)
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

class Art(db.Model):
	title = db.StringProperty(required = True)
	art = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class MainPage(Handler):
	def render_front(self, title="", art="", error=""):
		arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")


		self.render("front.html", title=title, art=art, error=error, arts = arts)

	def get(self):
		self.write(self.request.remote_addr)
		self.write(repr(get_coords(self.request.remote_addr)))
		return self.render_front()

	def post(self):
		title = self.request.get("title")
		art = self.request.get("art")

		if title and art:
			a = Art(title = title, art = art)
			#lookup the user's coords from their IP
			#if we have coordinates, add them to the Art
			a.put()

			self.redirect("/")
		else:
			error = "we need both a title and some artwork"
			self.render_front(title, art, error)

app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)