from flask import Flask
from flask import render_template
from glob import glob
import markdown
import myEmail
import myFiles
from os import getenv, path, walk
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
    # These are the file types supported by most browsers:
    imgTypes = [
        ".apng",
        ".avif",
        ".gif",
        ".jpg", 
        ".jpeg", 
        ".jfif", 
        ".pjpeg", 
        ".pjp",
        ".png",
        ".svg",
        ".webp"
    ]
    videoTypes = [
        ".ogg",
        ".mp4",
        ".webm"
    ]

    content = ""
    with open(staticFolder+str(year)+"/"+post+"/"+post) as f:
        content = f.read()
    content = markdown.markdown(content)
    
    files = sorted(myFiles.findFiles("*", where=staticFolder+f"{year}/{post}"))

    images = []
    videos = []
    for file in files:
        file_name, file_extension = path.splitext(file)
        ext = file_extension.lower()
        if ext in imgTypes:
            images.append(file)
        elif ext in videoTypes:
            videos.append(file)

    return content, images, videos

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
    textContent, images, videos = getPost(year, post)
    return render_template('post.html', MyName=getenv("MyName"), 
                            year=year, title=post, staticUrlPath=staticUrlPath,
                            textContent=textContent, images=images, videos=videos)
