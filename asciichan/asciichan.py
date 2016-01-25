import os

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

class MainPage(Handler):
	def get(self):
		self.render("front.html")

	def post(self):
		title = self.request.get("title")
		art = self.request.get("art")

		if title and art:
			self.write("thanks!")
		else:
			error = "we need both a title and some artwork"
			self.render("front.html", error = error)

app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)