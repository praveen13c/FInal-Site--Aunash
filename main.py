from flask import Flask, render_template, request, session, redirect
from flask import flash, url_for
import json

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import pymysql

from flask_mail import Mail
import os

from werkzeug.utils import secure_filename
from pathlib import Path
import math



with open("config.json", "r") as parm:
    params = json.load(parm)["params"]

with open("config.json", "r") as sgn:
    sign = json.load(sgn)['login']

with open("config.json", "r") as lmg:
    logmsg = json.load(lmg)['log_msg']

local_server=True
pymysql.install_as_MySQLdb()
app = Flask(__name__)
app.secret_key="ssk-super-secret-key-kss"
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT ='465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

class Contact(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    subheading = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    section01 = db.Column(db.String(300), nullable=True)
    section02 = db.Column(db.String(300), nullable=True)
    date = db.Column(db.String(12), nullable=True)
    author = db.Column(db.String(30), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)


class Quotes(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.String(30), nullable=False)
    author = db.Column(db.String(30), nullable=False)
    relation = db.Column(db.String(30), nullable=False)

class User(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    mobile = db.Column(db.String(30), nullable=False)
    date = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():

    return render_template("/index.html", params=params)


@app.route("/services")
def services():
    return render_template("/services.html", params=params)


@app.route("/blog")
def blog():
    posts = Posts.query.filter_by().all()

    last = math.ceil(len(posts)/params['no_of_posts'])
    page = request.args.get('page')

    if(not str(page).isnumeric()):
        page = 1

    page = int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):
                (page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    if(page==1):
        prev = "#"
        more = "/blog?page=" + str(page+1)
        endp = "/blog?page=" + str(last)
        begi = "/blog?page=" + str((page+1)-last)
    elif(page==last):
        prev = "/blog?page=" + str(page-1)
        more = "#"
        endp = "/blog?page=" + str(last)
        begi = "/blog?page=" + str((page+1)-last)
    else:
        prev = "/blog?page=" + str(page-1)
        more = "/blog?page=" + str(page+1)
        endp = "/blog?page=" + str(last)
        begi = "/blog?page=" + str((page+1)-last)
    return render_template("/blog.html",begi=begi, next=more, params=params, posts=posts,endp=endp, prev=prev )


@app.route("/posts/<string:post_slug>", methods=['GET'])
def post(post_slug):
    posts = Posts.query.filter_by(slug=post_slug).first()
    contact = Contact.query.all()
    return render_template("/posts.html", contact=contact, params=params, posts=posts)


@app.route("/vlog")
def vlog():

    return render_template("/vlog.html", params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        entry = Contact(name=name, email=email, phone_num=phone, message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        if email != "aunash.com@gmail.com":
            mail.send_message('New Message of ' + name + ' from Aunash ',
                            sender = email,
                            recipients = [params['gmail_user']],
                            body = message + '\n' + "Email of Sender : " + email + "   Phone : "+ phone
                              )
            
    return render_template("contact.html", params=params)

# ----------------------ADMIN CONTROL SECTION STARTS-------------------------------

# Dashboard or Admin Panel Section ( Sign in and other control)
@app.route("/dashboardans", methods=['GET', 'POST'])
def dashboard():

    if ('user' in session and session['user'] == sign['admin_name']):
        flash("welcome")
        posts = Posts.query.all()
        return render_template("dashboard.html",  params=params, sign=sign, posts=posts)

    if (request.method == 'POST'):

        userpass = request.form.get('pass')
        username = request.form.get('uname')

        if (username==sign['admin_name'] and userpass==sign['admin_pass']):
            flash("welcome")

            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html",  sign=sign, params=params, posts=posts)

    return render_template("signin.html", sign=sign, params=params)


# Logout Section
@app.route("/logout")
def logout():
    flash("bye")
    session.pop('user')
    return redirect("/dashboardans")
# Admin Section Ends -------------------------------------------
# Post Section Starts
# Post Control Panel
@app.route("/post_sec", methods=['GET', 'POST'])
def post_sec():

    if ('user' in session and session['user'] == sign['admin_name']):
        # flash("welcome")
        # posts = Posts.query.all()
        return render_template("admin-post.html",  params=params, sign=sign)

    return render_template("signin.html", sign=sign, params=params)


# Post Add Section
@app.route("/edit/<string:srno>", methods=['GET', 'POST'])
def edit(srno):

    if ('user' in session and session['user'] == sign['admin_name']):

        if request.method == "POST":
            title = request.form.get("title")
            subheading = request.form.get("subheading")
            slug = request.form.get("slug")
            content = request.form.get("content")
            img_file = request.form.get("img_file")
            section01 = request.form.get("section01")
            section02 = request.form.get("section02")
            author = request.form.get("author")
            date = datetime.now()
            if srno == '0':
                posts = Posts(title=title, slug=slug, content=content, subheading=subheading, section01=section01,
                              section02=section02, img_file=img_file, author=author, date=date)
                db.session.add(posts)
                db.session.commit()
            else:
                posts = Posts.query.filter_by(srno=srno).first()
                posts.title = title
                posts.slug = slug
                posts.content = content
                posts.shead = subheading
                posts.sec1 = section01
                posts.sec2 = section02
                posts.img_file = img_file
                posts.author = author
                posts.edate = date
                db.session.commit()

                # return redirect('/edit/'+srno)
                return redirect("/editdelete")
    posts = Posts.query.filter_by(srno=srno).first()
    return render_template("edit.html", params=params, posts=posts, srno=srno)

# Post Edit / Delete Section
@app.route("/editdelete", methods=['GET', 'POST'])
def editdelete():

    if ('user' in session and session['user'] == sign['admin_name']):
        flash("welcome")
        posts = Posts.query.all()
        return render_template("post-edit-del.html",  params=params, sign=sign, posts=posts)

    if (request.method == 'POST'):

        userpass = request.form.get('pass')
        username = request.form.get('uname')

        if (username==sign['admin_name'] and userpass==sign['admin_pass']):
            flash("welcome")

            session['user'] = username
            posts = Posts.query.all()
            return render_template("post-edit-del.html",  sign=sign, params=params, posts=posts)

    return render_template("signin.html", sign=sign, params=params)


# Post Delete Section
@app.route("/delete/<string:srno>", methods=['GET', 'POST'])
def delete(srno):

    if ('user' in session and session['user'] == sign['admin_name']):

        posts = Posts.query.filter_by(srno=srno).first()
        db.session.delete(posts)
        db.session.commit()
        return redirect("/dashboardans")
# Post Section Ends

# File Uploader Section
@app.route("/uploader", methods=['GET', 'POST'])
def uploader():

    if('user' in session and session['user'] == sign['admin_name']):
        if(request.method == "POST"):
            f=request.files['file1']
            my_file = Path(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            if my_file.is_file():
                return "File Already Exist ..." + str(my_file)
            elif f=="":
                return "Blank is not Valid option"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))

            return redirect("/dashboardans")
# Uploader Ends

# Quotation Section Starts
# Quote Section Main
@app.route("/quotesection", methods=['GET', 'POST'])
def quotesection():

    if ('user' in session and session['user'] == sign['admin_name']):
        flash("welcome")
        quotes = Quotes.query.all()
        return render_template("quotes.html",  params=params, sign=sign, quotes=quotes)

    if (request.method == 'POST'):

        userpass = request.form.get('pass')
        username = request.form.get('uname')

        if (username==sign['admin_name'] and userpass==sign['admin_pass']):
            flash("welcome")

            session['user'] = username
            quotes = Quotes.query.all()
            return render_template("quotes.html",  sign=sign, params=params, quotes=quotes)

    return render_template("signin.html", sign=sign, params=params)


# Quote Add
@app.route("/addquote/<string:srno>", methods=['GET', 'POST'])
def addquote(srno):

    if ('user' in session and session['user'] == sign['admin_name']):

        if request.method == "POST":
            quote = request.form.get("quote")
            relation = request.form.get("relation")
            author = request.form.get("author")

            if srno == '0':
                quotes = Quotes(quote=quote,author=author, relation=relation)
                db.session.add(quotes)
                db.session.commit()
            else:
                quotes = Quotes.query.filter_by(srno=srno).first()
                quotes.quote = quote
                quotes.author = author
                quotes.relation = relation
                db.session.commit()

                return redirect("/edquote")
    quotes = Quotes.query.filter_by(srno=srno).first()
    return render_template("editquote.html", params=params, quotes=quotes, srno=srno)

@app.route("/edquote", methods=['GET', 'POST'])
def edquote():

    if ('user' in session and session['user'] == sign['admin_name']):
        flash("welcome")
        quotes = Quotes.query.all()
        return render_template("quote-edit-del.html",  params=params, sign=sign, quotes=quotes)

    if (request.method == 'POST'):

        userpass = request.form.get('pass')
        username = request.form.get('uname')

        if (username==sign['admin_name'] and userpass==sign['admin_pass']):
            flash("welcome")

            session['user'] = username
            quotes = Quotes.query.all()
            return render_template("quote-edit-del.html",  params=params, sign=sign, quotes=quotes)

    return render_template("signin.html", sign=sign, params=params)


# Quote Delete Section
@app.route("/delquote/<string:srno>", methods=['GET', 'POST'])
def delquote(srno):

    if ('user' in session and session['user'] == sign['admin_name']):

        quotes = Quotes.query.filter_by(srno=srno).first()
        db.session.delete(quotes)
        db.session.commit()
        return redirect("/quotesection")
# Quote Section Ends
# Contact Messages Section Starts
@app.route("/contactall", methods=['GET', 'POST'])
def contactall():

    contact = Contact.query.all()
    return render_template("/contactall.html", contact=contact, params=params)
# End Contact & Messages list
# User Section Starts
@app.route("/userall", methods=['GET', 'POST'])
def userall():
    userlist = User.query.all()
    return render_template("/userall.html", userlist=userlist, params=params)
# End User list


# --------------------Admin Section Ends-------------------------------------------
app.run(debug=True)
