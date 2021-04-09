from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, Markup
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps



# MySQL ayarlari
app = Flask(__name__)
app.secret_key = 'our_blog?'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'ourblog'
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


#Kullanici Giris Decorator'i
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            message= Markup('Bu sayfayi görüntüleyebilmek icin lütfen <b>giris yapin!</b>')
            flash(message,'danger')
            return redirect(url_for('login'))
    return decorated_function


# Kullanici Kayit formu
class RegisterForm(Form):
    name = StringField('Isim Soyisim', validators=[
                       validators.Length(min=2, max=35)])
    username = StringField('Kullanici Adi', validators=[
                           validators.Length(min=2, max=30)])
    email = StringField('Email', validators=[validators.Email(
        message='Lütfen dogru bir email adresi girin...')])
    password = PasswordField('Parola', validators=[validators.DataRequired(
        message='Lütfen bir parola girin'), validators.EqualTo(fieldname='confirm', message='Parolaniz uyusmuyor')])
    confirm = PasswordField('Parola Tekrari', validators=[
                            validators.DataRequired(message='Lütfen ayni sifreyi girin...')])
    

# Kayit Olma
@app.route('/register', methods=['GET', 'POST'])
#def register():
#   form = RegisterForm(request.form)
#  if request.method == 'POST' and form.validate():
#      name = form.name.data
#    username = form.username.data
#   email = form.email.data
#   password = sha256_crypt.encrypt(form.password.data)
#   cursor = mysql.connection.cursor()
#   sorgu = 'INSERT INTO users (name,username,email,password) VALUES (%s,%s,%s,%s)'
#  cursor.execute(sorgu, (name, username, email, password))
#  mysql.connection.commit()
# cursor.close()
#  flash('Başarıyla Kayıt Oldunuz...', 'success')
#  return redirect(url_for('login'))
#  else:
#   return render_template('register.html', form=form)
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        # Exist User Control
        username = form.username.data
        email = form.email.data
        cursor = mysql.connection.cursor()
        # Username Check
        username_sorgu = "SELECT * FROM users WHERE username = %s"
        username_result = cursor.execute(username_sorgu, (username,))
        # Email Check
        email_sorgu = "SELECT * FROM users WHERE email = %s"
        email_result = cursor.execute(email_sorgu, (email,))

        if username_result > 0:
            flash("Böyle bir kullanıcı zaten mevcut.", "danger")
            return redirect(url_for("register"))
        elif email_result > 0:
            flash("Böyle bir email zaten mevcut.", "danger")
            return redirect(url_for("register"))
        else:
            name = form.name.data
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(form.password.data)

            cursor = mysql.connection.cursor()

            sorgu = "INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)"

            cursor.execute(sorgu, (name, username, email, password))
            mysql.connection.commit()
            cursor.close()
            flash("Başarıyla kayıt oldunuz!", category="success")
            return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)


# Kullanici Giris formu
class LoginForm(Form):
    username = StringField('Kullanici Adi')
    password = PasswordField('Parola')
    
    
# Login Giris yapma
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = 'SELECT * FROM users WHERE username = %s'

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data['password']
            real_user = data['name']
            if sha256_crypt.verify(password_entered, real_password):
                message = Markup(
                    f'Sayin <b>{real_user}</b>, basariyla giris yaptiniz. Sayfaniza Hosgeldiniz')
                flash(message, 'success')

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('index'))
            else:
                message = Markup('<b>Parolayi</b> yanlis girdiniz')
                flash(message, 'danger')
                return redirect(url_for('login'))

        else:
            message = Markup(
                f'<b>{username}</b> diye bir kullanici kayitlarimizda bulunmuyor')
            flash(message, 'danger')
            return redirect(url_for('login'))

    else:
        return render_template('login.html', form=form)


#Logout islemi
@app.route('/logout')
def logout():
    session.clear()

    message = Markup('Basariyla <b>cikis yaptiniz</b>. Tekrar görüsmek üzere')
    flash(message, 'success')

    return redirect(url_for('index'))


#Kontrol Paneli
@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = 'SELECT *FROM articles WHERE author = %s'

    result = cursor.execute(sorgu,(session['username'],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template('dashboard.html', articles=articles)
    else:
        return render_template('dashboard.html')


    
#Makale Ekleme
@app.route('/addarticle', methods=['GET', 'POST'])
@login_required
def addarticle ():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content =  form.content.data
        
        cursor = mysql.connection.cursor()
        
        sorgu = ' INSERT INTO articles(title,author,content) VALUES (%s,%s,%s)'
        
        cursor.execute(sorgu,(title, session['username'],content))
        
        mysql.connection.commit()
        
        cursor.close()
        
        flash('Makale basari ile eklendi.','success')
        
        return redirect(url_for('dashboard'))
    
    return render_template('addarticle.html',form=form)

class ArticleForm(Form):
    title = StringField('Makale Basligi',validators=[validators.Length(min=5,max=100)])
    content = TextAreaField('Makale Icerigi', validators=[validators.Length(min=10)])
    


#Makale sayfasi
@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()

    sorgu = 'SELECT *FROM articles'

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template('articles.html', articles=articles)

    else:
        return render_template('articles.html')



# Detay sayfalari
@app.route('/article/<string:id>')
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = 'SELECT *FROM articles WHERE id = %s'
    result = cursor.execute(sorgu, (id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template('article.html', article=article)
    else:
        return render_template('article.html')
    

#Makale Güncelleme
@app.route('/edit/<string:id>', methods=['GET', 'POST'])  # <string:id> dynamic url
@login_required

def edit(id):
    
    #GET REQUEST
    if request.method == 'GET':
        
        cursor = mysql.connection.cursor()

        sorgu = 'SELECT * FROM articles WHERE id = %s AND author = %s'
        
        result = cursor.execute(sorgu, (id, session['username']))
        
        if result == 0:
            flash('Böyle bir makale yok veya bu islemi yapmaya yetkili degilsiniz')
            return redirect(url_for('index'))
        
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article['title']
            form.content.data = article['content']
            return render_template('update.html', form = form)
    
    else:
        #POST REQUEST
        form = ArticleForm(request.form)
        
        newTitle = form.title.data
        newContent = form.content.data
        
        sorgu2 = 'UPDATE articles SET title = %s, content = %s WHERE id = %s'
        
        cursor =mysql.connection.cursor()
        
        cursor.execute(sorgu2, (newTitle,newContent,id))
        
        mysql.connection.commit()
        
        flash('Makale basari ile güncellendi','success')
        
        return redirect(url_for('dashboard'))
        
        

#Makale Silme
@app.route(('/delete/<string:id>'))
@login_required

def delete(id):
    
    cursor = mysql.connection.cursor()
    
    sorgu = 'SELECT * FROM articles WHERE author = %s AND id = %s'
    
    result = cursor.execute(sorgu, (session['username'],id))
    
    if result > 0:
        sorgu2 = 'DELETE FROM articles WHERE id = %s'
        cursor.execute(sorgu2, (id,))
        mysql.connection.commit()
        return redirect(url_for('dashboard'))
        
    else:
        flash('Böyle bir makale yok veya bu isleme yetkiniz yok','danger')
        return redirect(url_for('index'))
        
#Arama url
@app.route('/search',methods=['GET','POST'])
def search():
   if request.method == 'GET' :
       return redirect(url_for('index'))  
   else:
       keyword = request.form.get('keyword') 
       
       cursor = mysql.connection.cursor()
       
       sorgu = f'SELECT * FROM articles WHERE title LIKE "%{keyword}%" OR content LIKE "%{keyword}%"'
       
       result = cursor.execute(sorgu)
       
       if result == 0:
           flash('Aranan kelimeye uygun makale bulunamadi!','warning')
           return redirect(url_for('articles'))
       else:
           articles = cursor.fetchall()
           return render_template('articles.html', articles = articles)
    
    
if __name__ == '__main__':
    app.run(debug=True)

def new_func():
    return
