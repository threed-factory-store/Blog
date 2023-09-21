# Blog

This is a self-hosted blog.  It is intended to be super simple to use and maintain.  It has no database.  It's written in Python so if your hosting provider has Python accessible to you, all you have to do is copy your files to the server and make sure a few Python packages are installed.  It assumes it's running on Linux because duh.

Posts are organized by year and date.  The main page shows a list of years, newest first.  Click one and you see a list of blog posts for that year, again newest first.  Click one and you read the post.  Maybe someday the main page will take one image from each of the most recent posts and show them with links to their posts.

You post to it by sending an email.  The subject is the blog post title.  The body of the email is the body of the post.  You can attach jpgs to the email.

Emails are processed by the web code.  There is no cron job.  When someone visits the main page, we look to see if there are new emails.  There are crude checks to make sure only one app is processing emails at a time, but they're not great.

There is no admin interface or login.  If you want to delete a post or make any other changes, login to your hosting provider and change things.

Python packages:
pip install Flask
pip install python-dotenv
pip install Markdown


Configuration settings are in environment variables.  Search the code for "getenv(" and add them to a .env file.
