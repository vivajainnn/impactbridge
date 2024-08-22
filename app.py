from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = '84509'  # Set your secret key here

# Set up the connection
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='impact',
    database='website'
)

# Create a cursor object to interact with the database
cursor = connection.cursor(dictionary=True, buffered=True)

@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_type = request.form['user_type']
        
        if user_type == 'ngo':
            email = request.form['email1']
            password= request.form['password1']
            ngo_name = request.form['ngo_name1']
            description = request.form['description']
            
            # Insert into NGOs table
            cursor.execute("INSERT INTO ngos (name, description) VALUES (%s, %s)", (ngo_name, description))
            connection.commit()
            ngo_id = cursor.lastrowid
            
            # Insert into users table with NGO reference
            cursor.execute("INSERT INTO users ( email, password, user_type, ngo_id) VALUES (%s, %s, %s, %s)", 
                           ( email, password, user_type, ngo_id))
            connection.commit()
            return redirect(url_for('explore'))
        else:
            email = request.form['email']
            password = request.form['password']

            # Insert into users table for volunteers
            cursor.execute("INSERT INTO users ( email, password, user_type) VALUES (%s, %s, %s)", 
                           (email, password, user_type))
            connection.commit()
        
            return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['user_type'] = user['user_type']
            
            if user['user_type'] == 'ngo':
                session['ngo_id'] = user['ngo_id']
                return redirect(url_for('explore'))
            else:
                return redirect(url_for('home'))
        else:
            return "Invalid email or password"
    
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/explore')
def explore():
    # Fetch all posts and associated NGOs
    cursor.execute("""
        SELECT ngos.name AS ngo_name, posts.content , posts.posted_by
        FROM posts
        JOIN ngos ON ngos.id = posts.ngo_id
    """)
    posts = cursor.fetchall()
    return render_template('explore.html', posts=posts)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    cursor.execute("""
        SELECT ngos.name AS ngo_name, posts.content 
        FROM posts
        JOIN ngos ON ngos.id = posts.ngo_id
        WHERE ngos.name LIKE %s OR posts.content LIKE %s
    """, (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    return render_template('explore.html', posts=results)

@app.route('/post', methods=['POST'])
def post():
    content = request.form['post_content']
    ngo_id = session.get('ngo_id') 
    user_id = session.get('user_id')
    posted_by = session.get('user_type')
    

    if posted_by == 'ngo':
       #posted_by= 'NGO'
        cursor.execute("INSERT INTO posts (ngo_id, content, posted_by) VALUES (%s, %s, %s)", (ngo_id, content, posted_by))
        
    else:
        #posted_by= 'Volunteer'
        cursor.execute("INSERT INTO posts (id, content, posted_by) VALUES (%s, %s, %s)", (user_id, content, posted_by))
        
    connection.commit()
    return redirect(url_for('explore'))

@app.route('/profiles', methods=['GET', 'POST'])
def profiles():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('register'))

    user_id = session['user_id']

    if request.method == 'POST':
        # Get data from the form
        name = request.form['name']
        qualifications = request.form['qualifications']
        availability = request.form['availability']
        location = request.form['location']
        experience = request.form['experience']
        skills = request.form['skills']
        education = request.form['education']

        # Check if a profile already exists for this user
        cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()

        if profile:
            # Update the existing profile
            cursor.execute("""
                UPDATE profiles SET 
                name = %s, qualifications = %s, availability = %s, 
                location = %s, experience = %s, skills = %s, education = %s
                WHERE user_id = %s
            """, (name, qualifications, availability, location, experience, skills, education, user_id))
        else:
            # Insert a new profile
            cursor.execute("""
                INSERT INTO profiles 
                (name, qualifications, availability, location, experience, skills, education, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, qualifications, availability, location, experience, skills, education, user_id))

        connection.commit()
        return redirect(url_for('profiles'))

    # Fetch the existing profile if it exists
    cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
    profile = cursor.fetchone()

    return render_template('profiles.html', profile=profile)

if __name__ == '__main__':
    app.run(debug=True)
