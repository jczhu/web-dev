import os
import re
import hmac
import hashlib
import random
import json
from datetime import datetime
from string import letters

import jinja2
import webapp2

from google.appengine.api import memcache
from google.appengine.ext import db

secret = "Imsosecret"
key = 'top'
last_queried = datetime.now()

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

def top_entries():
	entries = memcache.get(key)
	if entries is None:
		last_queried = datetime.now()
		entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC LIMIT 10")
		entries = list(entries)
		memcache.set(key=key, value=entries)
	return entries

class MainPage(Handler):
	def get(self):
		entries = top_entries()
		age = datetime.now() - last_queried

		self.render("front.html", entries = entries, age=round(age.total_seconds(), 0))

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

			#rerun the query and update cache by deleting key from cache
			memcache.delete(key=key)

			self.redirect("/"+str(e.key().id()))
		else:
			error = "we need both a title and a blog entry"
			self.render_newpost(title, entry, error)

class BlogPost(Handler):
	def get(self, entry_id):
		e = Entry.get_by_id(int(entry_id))
		self.render("single-entry.html", entry=e)

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()

class SignUp(Handler):
	def render_form(self, username="", invalid_user="", invalid_pass="", diff_pass="", 
		invalid_email=""):
		self.render("signup.html", username=username, invalid_user=invalid_user,
			invalid_pass=invalid_pass, diff_pass=diff_pass, invalid_email=invalid_email)

	def get(self):
		self.render_form()

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')

		check_username = valid_username(username)
		check_password = valid_password(password)
		check_verify = (password == verify)
		check_email = valid_email(email)

		user_error, pass_error, verify_error, email_error = "", "", "", ""
		if not check_username:
			user_error = "That's not a valid username."
		elif User.get_by_key_name(username):
			user_error = "That username already exists"
		if not check_password:
			pass_error = "That's wasn't a valid password."
		if not check_verify:
			verify_error = "Your passwords didn't match."
		if not check_email:
			email_error = "That's not a valid email."

		if check_username and check_password and check_verify and check_email and not User.get_by_key_name(username):

			pass_hash = make_pw_hash(username, password)
			u = User(key_name=username, username=username, password=pass_hash, email=email)
			u.put()

			# making cookie for username
			self.response.headers['Content-Type']='text/plain'
			new_cookie_val = make_secure_val(username)
			self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/'
				%str(new_cookie_val))

			self.redirect("/welcome") 
		else:
			self.render_form(username, user_error, pass_error, verify_error, email_error)

class Login(Handler):
	def render_login(self, error=""):
		self.render("login.html", error=error)

	def get(self):
		self.render_login()

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')

		if not User.get_by_key_name(username):
			self.render_login(error="Invalid login")
		else:
			if valid_pw(username, password, User.get_by_key_name(username).password):
				new_cookie_val = make_secure_val(username)
				self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/'
					%str(new_cookie_val))

				self.redirect("/welcome")
			else:
				self.render_login(error="Invalid login")

class Logout(Handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'name=""; Path=/')
		self.redirect('/signup')

class Welcome(Handler):
	def get(self):
		name_cookie = self.request.cookies.get('name')
		if name_cookie:
			name_val = check_secure_val(name_cookie)
			if name_val:
				self.response.out.write("Welcome, %s!"%name_val)
			else:
				self.redirect('/signup')
		else:
			self.redirect('/signup')

class JsonHandler(Handler):
	def get(self, entry_id= -1):
		if entry_id == -1:
			entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC LIMIT 10")
			entries = list(entries)
			list_dict = []
			for e in entries:
				d = {}
				d["title"] = e.title
				d["entry"] = e.entry
				d["created"] = e.created.strftime('%B %d, %Y')
				list_dict.append(d)

			list_dict = json.dumps(list_dict)

			self.render("json.html", entries=list_dict)
		
		else:
			e = Entry.get_by_id(int(entry_id))
			list_dict = []
			d = {}
			d["title"] = e.title
			d["entry"] = e.entry
			d["created"] = e.created.strftime('%B %d, %Y')
			list_dict.append(d)

			list_dict = json.dumps(list_dict)

			self.render("json.html", entries=list_dict)

		

def hash_str(s):
	return hmac.new(secret, s).hexdigest()

def make_secure_val(s):
	return "%s|%s" %(s, hash_str(s))

def check_secure_val(h):
	s = h.split('|')[0]
	if h == make_secure_val(s):
		return s

def make_salt(length = 5):
	return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split(',')[0]
	return h == make_pw_hash(name, password, salt)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
	return USER_RE.match(username)

def valid_password(password):
	return PASS_RE.match(password)

def valid_email(email):
	return EMAIL_RE.match(email) or email == ''

app = webapp2.WSGIApplication([
	('/', MainPage), ('/newpost', NewPost), (r'/(\d+)', BlogPost), ('/signup', SignUp), 
	('/welcome', Welcome), ('/login', Login), ('/logout', Logout), 
	(r'/(\d*)/.json', JsonHandler), ('/.json', JsonHandler)
], debug=True)