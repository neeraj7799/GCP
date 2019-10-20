from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
import mysql.connector
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
import pandas as pd
from functools import wraps
app= Flask(__name__,template_folder='template')

# config my sql
def Articles():
    article=[
    {
        'id':1,
        'title':'Article One',
        'body':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusantium deserunt dolore dolores earum, eveniet hic qui quo tempora velit. Ad dolorem, enim esse ipsa itaque laudantium quibusdam saepe. Perferendis, quam!',
        'author':'Brad Traversy',
        'created_date':'12-12-2018'
    },
    {
    'id':2,
        'title':'Article two',
        'body':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusantium deserunt dolore dolores earum, eveniet hic qui quo tempora velit. Ad dolorem, enim esse ipsa itaque laudantium quibusdam saepe. Perferendis, quam!',
        'author':'John Doe',
        'created_date':'12-12-2018'
    }
    ]
    return article

mysqls=mysql.connector.connect(host='db',user='root',password='hudsondata',database='myflaskapp',port='3306')

Articles=Articles()
@app.route('/')
def index():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/articles')
def articles():
    articles=pd.DataFrame()
    cur = mysqls.cursor()
    cur.execute("Select * from myflaskapp.articles")
    articles = cur.fetchall()

    if len(articles) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    cur.close()
@app.route('/article/<string:id>/')
def article(id):
    cur=mysqls.cursor()
    cur.execute("select * from myflaskapp.articles where id=%s",[id])
    article=cur.fetchone()


    return render_template('article.html',article=article)
@app.route('/articles')



class RegisterForm(Form):
    name= StringField('Name', [validators.Length(min=1,max=50)])
    username=StringField('Email', [validators.Length(min=4,max=25)])
    email=StringField('Username', [validators.Length(min=6,max=50)])
    password=StringField('Password', [validators.DataRequired(),validators.EqualTo('confirm',message='Passwords do not match')])
    confirm=PasswordField('Confirm Password')
@app.route('/register',methods=['GET','POST'])
def register():
    form= RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur= mysqls.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
        mysqls.commit()
        cur.close()
        flash("You are now registered and can log in",'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# login
@app.route('/login',methods=['GET','POST'])
def login():
    result=pd.DataFrame()
    if request.method =='POST':
        username= request.form['username']
        password_candidate= request.form['password']

        cur=mysqls.cursor()
        cur.execute('select * from myflaskapp.users where username="{}"'.format(username))
        result=cur.fetchall()





        if len(result)>0:
            data=result[0]
            print(data)
            passwords=data[4]
            # passwords=sha256_crypt.encrypt(data['password'])
            # print(passwords)

            if sha256_crypt.verify(password_candidate,passwords):
                session['logged_in']=True
                session['username']=username
                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error='Invalid login'
                return render_template('login.html',error=error)

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
        cur.close()
    return render_template('login.html')
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    articles = pd.DataFrame()
    cur=mysqls.cursor()
    cur.execute("Select * from myflaskapp.articles")
    articles=cur.fetchall()
    print(articles)
    if len(articles)>0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg='No Articles Found'
        return render_template('dashboard.html',msg=msg)
    cur.close()

# article form class
class ArticleForm(Form):
    title= StringField('Title', [validators.Length(min=1,max=200)])
    body=TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title = form.title.data
        body= form.body.data

        cur=mysqls.cursor()
        cur.execute("INSERT INTO myflaskapp.articles(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))
        mysqls.commit()
        cur.close()
        flash('Article created','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)

@app.route('/edit_articles/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_articles(id):
    # create cursor
    cur=mysqls.cursor()
    cur.execute("select * from myflaskapp.articles WHERE id =%s",[id])
    article =cur.fetchone()

    # Get form

    form = ArticleForm(request.form)
    form.title.data=article[1]
    form.body.data=article[3]
    if request.method=='POST' and form.validate():
        title = request.form['title']
        body= request.form['body']
        cur=mysqls.cursor()
        cur.execute("UPDATE myflaskapp.articles "
                    "SET title=%s, body=%s "
                    "WHERE id =%s", (title,body,id))
        mysqls.commit()
        cur.close()
        flash('Article updated','success')
        return redirect(url_for('dashboard'))
    cur.close()
    return render_template('edit_articles.html',form=form)
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    cur=mysqls.cursor()
    cur.execute("DELETE FROM myflaskapp.articles WHERE id=%s",[id])
    cur.close()
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))


if __name__=='__main__':
    app.secret_key='secret123'
    app.run(host= '0.0.0.0',port=5000,debug=True)