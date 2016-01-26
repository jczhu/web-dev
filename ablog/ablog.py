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


class Entry(db.Model):
	title = db.StringProperty(required = True)
	entry = db.TextProperty(required = True)
	created = db.DateProperty(auto_now_add = True)

class MainPage(Handler):
	def get(self):
		entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created ASC")

		self.render("front.html", entries = entries)

class NewPost(Handler):
	def render_newpost(self, title="", entry="", error=""):
		self.render("newpost.html", title=title, entry=entry, error=error)

	def get(self):
		self.render_newpost()

	def post(self):
		title = self.request.get("title")
		entry = self.request.get("entry")

		if title and entry:
			e = Entry(title = title, entry = entry)
			e.put()

			self.redirect("/")
		else:
			error = "we need both a title and a blog entry"
			self.render_newpost(title, entry, error)

class BlogPost(Handler):
	def get(self, entry_id):
		e = Entry.get_by_id(int(entry_id))
		self.render("single-entry.html", entry=e)

app = webapp2.WSGIApplication([
    ('/', MainPage), ('/newpost', NewPost), (r'/(\d+)', BlogPost)
], debug=True)