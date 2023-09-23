import datetime
from flask import Flask, render_template, make_response
from glob import glob
import markdown
import myEmail
import myFiles
from os import getenv, path, walk
from dotenv import load_dotenv
import time

load_dotenv() 

staticFolder="./static/"
staticUrlPath="/static/"

app = Flask(__name__, static_url_path=staticUrlPath)

def getYears(): 
    result = sorted(next(walk(staticFolder))[1], reverse=True)
    return result

def getPosts(year):
    yearFolder = staticFolder+f"{year}"
    folders = glob("*", root_dir=yearFolder, recursive = False)

    # We want to show posts newest first.
    # If we just call sorted on folders, the posts on one day will be sorted in alphabetical order.
    # So we have to get the modified datetime of the folders and sort on that.
    result = {}
    for folder in folders:
        modified = time.gmtime(path.getmtime(yearFolder+"/"+folder))
        result[modified] = folder
    result = dict(sorted(result.items(), reverse=True))
    result = list(result.values())

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
    years = getYears()
    thisYear = datetime.date.today().year
    newPosts = 0
    if years and int(years[0]) < thisYear:
        newPosts = myEmail.newMailCount()

    response = make_response(render_template('index.html', MyName=getenv("MyName"), years=years, newPosts=newPosts))
    if newPosts:
        myEmail.processEmails(staticFolder, response)

    return response


@app.route("/posts/<int:year>/")
def posts(year=None):
    posts = getPosts(year)

    thisYear = datetime.date.today().year
    newPosts = 0
    if year == thisYear:
        newPosts = myEmail.newMailCount()

    response = make_response(render_template('year.html', MyName=getenv("MyName"), year=year, posts=posts, newPosts=newPosts))
    if newPosts:
        myEmail.processEmails(staticFolder, response)

    return response


@app.route("/posts/<int:year>/<post>/")
def onePost(year, post):
    textContent, images, videos = getPost(year, post)
    return render_template('post.html', MyName=getenv("MyName"), 
                            year=year, title=post, staticUrlPath=staticUrlPath,
                            textContent=textContent, images=images, videos=videos)
