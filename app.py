from flask import Flask
from flask import render_template
from glob import glob
from html import escape 
import markdown
import myEmail
import myFiles
from os import getenv, walk
from dotenv import load_dotenv

load_dotenv() 

staticFolder="./static/"
staticUrlPath="/static/"

app = Flask(__name__, static_url_path=staticUrlPath)

def getYears(): 
    result = sorted(next(walk(staticFolder))[1], reverse=True)
    return result

def getPosts(year):
    result = sorted(glob("*", root_dir=staticFolder+f"{year}", recursive = False), reverse=True)
    return result

def getPost(year, post):
    content = ""
    with open(staticFolder+str(year)+"/"+post+"/"+post) as f:
        content = f.read()
    result = markdown.markdown(content)
    
    images = sorted(myFiles.findFiles("*", where=staticFolder+f"{year}/{post}"))

    if images:
        imageHtml=False
        for imageFilename in images:
            if imageFilename == post:
                continue
            imageHtml = imageHtml or "<ul id='images' class='no-bullets'>"
            imageHtml += "<li><img src='"+staticUrlPath+f"{year}/{post}/{imageFilename}' width='80%'></li>"
        imageHtml+="</ul>"
        result += imageHtml

    return result

@app.route("/")
@app.route("/posts/")
def mainPage():
    # hasEmail = myEmail.emailExists()
    years = getYears()
    return render_template('index.html', MyName=getenv("MyName"), years=years)

@app.route("/posts/<int:year>/")
def posts(year=None):
    posts = getPosts(year)
    return render_template('year.html', MyName=getenv("MyName"), year=year, posts=posts)

@app.route("/posts/<int:year>/<post>/")
def onePost(year, post):
    content = getPost(year, post)
    return render_template('post.html', MyName=getenv("MyName"), year=year, title=post, post=content)
