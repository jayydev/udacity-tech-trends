import sqlite3
import logging
import sys


from flask import Flask, json, render_template, request, url_for, redirect, flash

logger = None
db_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    """Creates and returns a db connecion"""
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    global db_connection_count
    db_connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    """Queries a post for a given post id"""
    get_post_connection = get_db_connection()
    post_row = get_post_connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    get_post_connection.close()
    return post_row

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    """Returns all post detailss"""
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    """Returns the post for the give post id"""
    ret_post = get_post(post_id)
    if post is None:        
        logger.error("Article for post id %i does not exist! a 404 page is returned", post_id)
        return render_template('404.html')
    else:
        logger.info("Article %s retrieved!", ret_post['title'])
        return render_template('post.html', post=ret_post)

# Define the About Us page
@app.route('/about')
def about():
    """Returns about us page"""

    logger.info("The \"About Us\" page is retrieved.")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    """Creates a post"""

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
            connection.commit()
            connection.close()

            logger.info("Article %s is created.", title)
            
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthz():
    """Returns health status"""
    logger.info("healthz called")
    result = 'Ok - healthy'
    status = 200
    try:
        conn = get_db_connection()
        conn.execute('SELECT count(*) FROM posts')
    except sqlite3.DatabaseError as error:    
        logger.error("Failed to connect to datavase. Error = %s", error.args)
        result = 'ERROR - unhealthy'
        status = 500
    
    response = app.response_class(
    response = json.dumps({'result' : result}), 
    status = status,
    mimetype="application/json"
    )
    return response

@app.route('/metrics')
def metrics():
    """Returns metrics"""
    logger.info("metrics called")   
    
    connection = get_db_connection()
    post_count = connection.execute('SELECT count(*) FROM posts').fetchone()
      
    response = app.response_class(
    response = json.dumps({"db_connection_count": db_connection_count, "post_count": post_count[0]}), 
    status = 200,
    mimetype="application/json"
    )

    connection.close()
    return response


def setup_logger():    
    """Sets up a logger"""
    
    log_file_handler = logging.FileHandler('tech_trend_log.txt')
    std_out_handler = logging.StreamHandler(stream=sys.stdout)    
    std_error_handler = logging.StreamHandler(stream=sys.stderr)
    logging.basicConfig(format='%(levelname)s %(asctime)-8s %(message)s', datefmt='%d/%m/%Y, %H:%M:%S', level=logging.DEBUG, 
    handlers={log_file_handler, std_out_handler, std_error_handler})
    return logging.getLogger("app")

# start the application on port 3111
if __name__ == "__main__":
    logger = setup_logger()
    app.run(host='0.0.0.0', port='3111')
