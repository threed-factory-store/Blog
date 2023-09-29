import datetime
from flask import Flask, render_template, make_response, url_for
from glob import glob
import markdown
import myEmail
import myFiles
from os import getenv, path, walk
from dotenv import load_dotenv
import time

load_dotenv() 
staticUrlPath = "/static/"

app = Flask(__name__, static_url_path=staticUrlPath)

staticFolder = path.join("./static", "")


def getYears(): 
    result = sorted(next(walk(staticFolder))[1], reverse=True)
    return result

def getPosts(year):
    yearFolder = path.join(staticFolder, f"{year}")
    postFolders = glob(path.join(yearFolder,"*"), recursive = False)

    # We want to show posts newest first.
    # If we just call sorted on posts, the posts on one day will be sorted in alphabetical order.
    # So we have to get the modified datetime of the folders and sort on that.
    result = {}
    for postFolder in postFolders:
        modified = path.getmtime(postFolder)
        result[modified] = postFolder.replace(path.join(yearFolder,""), "")
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
    try:
        postFileName = staticFolder+str(year)+"/"+post+"/"+post
        with open(postFileName) as f:
            content = f.read()
    except:
        pass
        # content="File not found '"+postFileName+"'"
    content = markdown.markdown(content)
    
    files = sorted(myFiles.findFiles("*", where=staticFolder+f"{year}/{post}"))

    images = []
    videos = []
    if files:
        for file in files:
            file_name, file_extension = path.splitext(file)
            ext = file_extension.lower()
            if ext in imgTypes:
                images.append(file)
            elif ext in videoTypes:
                videos.append(file)

    return content, images, videos


@app.route("/posts/")
@app.route("/")
def mainPage():
    years = getYears()
    thisYear = datetime.date.today().year
    newPosts = 0
    # Only show the "New Posts" blurb if it would result in the user seeing something new...
    if years and int(years[0]) < thisYear:
        newPosts = myEmail.newMailCount()

    response = make_response(render_template('index.html', MyName=getenv("MyName"), years=years, newPosts=newPosts))

    # If we didn't check for new posts above, do it now.
    # processEmails is something we only want to do if there are actually new emails.
    if not (years and int(years[0]) < thisYear):
        newPosts = myEmail.newMailCount()

    if newPosts:
        myEmail.processEmails(staticFolder, response)

    return response


@app.route("/posts/<int:year>/")
def posts(year=None):
    posts = getPosts(year)

    thisYear = datetime.date.today().year
    newPosts = 0
    # Only show the "New Posts" blurb if it would result in the user seeing something new...
    if year == thisYear:
        newPosts = myEmail.newMailCount()

    response = make_response(render_template('year.html', MyName=getenv("MyName"), 
                                             year=year, posts=posts, newPosts=newPosts))
    if newPosts:
        myEmail.processEmails(staticFolder, response)

    return response


@app.route("/posts/<int:year>/<post>/")
def onePost(year, post):
    textContent, images, videos = getPost(year, post)
    return render_template('post.html', MyName=getenv("MyName"), 
                           yearUrl=url_for('posts', year=year).replace("/index.cgi", ''),
                            year=year, title=post, staticUrlPath=staticUrlPath,
                            textContent=textContent, images=images, videos=videos)
