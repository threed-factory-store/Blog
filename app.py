from flask import Flask
from flask import render_template
from glob import glob
from html import escape 
import markdown
import myEmail
import myFiles

rootFolder="./posts/"
staticFolder="./static/"
staticUrlPath="/static/"

app = Flask(__name__, static_url_path=staticUrlPath)

def getYears():
    result = sorted(glob("*", root_dir=rootFolder, recursive = False), reverse=True)
    return result

def getPosts(year):
    result = sorted(glob("*", root_dir=rootFolder+f"{year}", recursive = False), reverse=True)
    return result

def getPost(year, post):
    content = ""
    with open(rootFolder+str(year)+"/"+post+"/"+post) as f:
        content = f.read()
    result = markdown.markdown(content)
    
    images = sorted(myFiles.findFiles("*.jpg", where=staticFolder+f"{year}/{post}"))

    imageHtml=""
    if images:
        imageHtml="<ul id='images'>"
        for image in images:
            imageHtml += "<li><img src='"+staticUrlPath+f"{year}/{post}/{image}' width='500'></li>"
        imageHtml+="</ul>"

    result += imageHtml
    return result

@app.route("/")
@app.route("/posts/")
def mainPage():
    # hasEmail = myEmail.emailExists()
    years = getYears()
    return render_template('index.html', years=years)

@app.route("/posts/<int:year>")
def posts(year=None):
    posts = getPosts(year)
    return render_template('year.html', year=year, posts=posts)

@app.route("/posts/<int:year>/<post>")
def onePost(year, post):
    content = getPost(year, post)
    return render_template('post.html', year=year, post=content)
