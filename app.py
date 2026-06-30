import psycopg2
from  psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import webbrowser

app = Flask(__name__)
app.secret_key = 'cinema_insight_secret_key_2024'
# D
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres.wgjwhqeqfaftguvtypma:Pankaj_rala%402008@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

def get_db():
    return psycopg2.connect(DATABASE_URL)


# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT COUNT(*) AS count FROM movies")
    total_movies = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) AS count FROM reviews")
    total_reviews = cur.fetchone()['count']

    cur.execute("SELECT AVG(rating) AS avg_rating FROM movies")
    avg_rating = round(cur.fetchone()['avg_rating'] or 0, 1)

    cur.execute("SELECT COUNT(DISTINCT genre) AS count FROM movies")
    total_genres = cur.fetchone()['count']

    stats = {
    'total_movies': total_movies,
    'total_reviews': total_reviews,
    'avg_rating': avg_rating,
    'total_genres': total_genres
}
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
    SELECT m.*, COALESCE(AVG(r.rating), m.rating) AS avg_rating
    FROM movies m
    LEFT JOIN reviews r ON m.id = r.movie_id
    GROUP BY m.id
    ORDER BY avg_rating DESC
    LIMIT 6
''')

    top_movies = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', stats=stats, top_movies=top_movies)

@app.route('/browse')
def browse():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
        SELECT
            m.*,
            COALESCE(AVG(r.rating), m.rating) AS avg_rating,
            COUNT(r.id) AS review_count
        FROM movies m
        LEFT JOIN reviews r ON m.id = r.movie_id
        GROUP BY m.id
        ORDER BY m.title
    ''')

    movies = cur.fetchall()

    cur.execute('''
        SELECT DISTINCT genre
        FROM movies
        ORDER BY genre
    ''')

    genres = cur.fetchall()

    watchlist_ids = []

    if 'user_id' in session:
        cur.execute(
            "SELECT movie_id FROM watchlist WHERE user_id=%s",
            (session['user_id'],)
        )

        rows = cur.fetchall()

        watchlist_ids = [row['movie_id'] for row in rows]

    cur.close()
    conn.close()

    return render_template(
        'browse.html',
        movies=movies,
        genres=genres,
        watchlist_ids=watchlist_ids
    )

@app.route('/reviews')
def reviews():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
    SELECT rv.*, u.username, u.full_name, m.title AS movie_title
    FROM reviews rv
    JOIN users u ON rv.user_id = u.id
    JOIN movies m ON rv.movie_id = m.id
    ORDER BY rv.created_at DESC
''')

    all_reviews = cur.fetchall()

    cur.execute(
    "SELECT id, title FROM movies ORDER BY title"
    )

    movies = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('reviews.html', reviews=all_reviews, movies=movies)

@app.route('/watchlist')
def watchlist():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
    SELECT m.*, w.added_at
    FROM watchlist w
    JOIN movies m ON w.movie_id = m.id
    WHERE w.user_id = %s
    ORDER BY w.added_at DESC
    ''', (session['user_id'],))

    items = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('watchlist.html', items=items)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM users WHERE id = %s",
        (session['user_id'],)
    )

    user = cur.fetchone()

    cur.execute('''
        SELECT rv.*, m.title AS movie_title
        FROM reviews rv
        JOIN movies m ON rv.movie_id = m.id
        WHERE rv.user_id = %s
        ORDER BY rv.created_at DESC
    ''', (session['user_id'],))

    user_reviews = cur.fetchall()

    cur.execute('''
        SELECT m.*
        FROM watchlist w
        JOIN movies m ON w.movie_id = m.id
        WHERE w.user_id = %s
        ORDER BY w.added_at DESC
    ''', (session['user_id'],))

    user_watchlist = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'profile.html',
        user=user,
        user_reviews=user_reviews,
        user_watchlist=user_watchlist
    )

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    identifier = data.get('identifier', '').strip()
    password = data.get('password', '').strip()
    
    if not identifier or not password:
        return jsonify({'success': False, 'message': 'Please fill in all fields'}), 400
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM users WHERE LOWER(username)=LOWER(%s) OR LOWER(email)=LOWER(%s) LIMIT 1",
        (identifier, identifier)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'email': user['email']
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('index.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         data = request.get_json() or request.form
#         full_name = data.get('full_name', '').strip()
#         username = data.get('username', '').strip()
#         email = data.get('email', '').strip()
#         phone = data.get('phone', '').strip()
#         password = data.get('password', '').strip()
#         if not all([full_name, username, email, password]):
#             return jsonify({'success': False, 'message': 'All fields are required'}), 400
        # conn = get_db()
        # existing = conn.execute(
        #     "SELECT id FROM users WHERE username=? OR email=?", (username, email)
        # ).fetchone()
        # if existing:
        #     conn.close()
        #     return jsonify({'success': False, 'message': 'Username or email already exists'}), 409
        # conn.execute('''INSERT INTO users (full_name, username, email, phone, password)
        #                 VALUES (?,?,?,?,?)''',
        #              (full_name, username, email, phone, generate_password_hash(password)))
        # conn.commit()
        # user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        # conn.close()
        
#     try:
#         conn = get_db()
#         cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

#         print("Checking existing user...")

#     cur.execute(
#         "SELECT id FROM users WHERE username=%s OR email=%s",
#         (username, email)
#     )

#     existing = cur.fetchone()

#     if existing:
#         cur.close()
#         conn.close()

#         return jsonify({
#             'success': False,
#             'message': 'Username or email already exists'
#         }), 409

#     print("Inserting user...")

#     cur.execute(
#         '''
#         INSERT INTO users (full_name, username, email, phone, password)
#         VALUES (%s, %s, %s, %s, %s)
#         RETURNING id, username, full_name
#         ''',
#         (
#             full_name,
#             username,
#             email,
#             phone,
#             generate_password_hash(password)
#         )
#     )

#     user = cur.fetchone()

#     print("Inserted User:", user)

#     conn.commit()

#     cur.close()
#     conn.close()
# except Exception as e:

# if 'conn' in locals():
#         conn.rollback()
#         conn.close()
#         print("REGISTER ERROR:", e)
#    return jsonify({
#         'success': False,
#         'message': str(e)
#     }), 500 
#     session['user_id'] = user['id']
#     session['username'] = user['username']
#     session['full_name'] = user['full_name']
#     return jsonify({'success': True, 'message': 'Registration successful'})
#     return render_template('register.html')

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    full_name = data.get('full_name', '').strip()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()

    if not all([full_name, username, email, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT id FROM users WHERE LOWER(username)=LOWER(%s) OR LOWER(email)=LOWER(%s)",
            (username, email)
        )
        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Username or email already exists'}), 409

        cur.execute(
            '''
            INSERT INTO users (full_name, username, email, phone, password)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, username, full_name, email
            ''',
            (full_name, username, email, phone, generate_password_hash(password))
        )

        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'email': user['email']
            }
        })

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() or request.form

        full_name = data.get('full_name', '').strip()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()

        if not all([full_name, username, email, password]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400

        try:
            conn = get_db()

            cur = conn.cursor(cursor_factory=RealDictCursor)

            print("Checking existing user...")

            cur.execute(
                "SELECT id FROM users WHERE username=%s OR email=%s",
                (username, email)
            )

            existing = cur.fetchone()

            if existing:
                cur.close()
                conn.close()

                return jsonify({
                    'success': False,
                    'message': 'Username or email already exists'
                }), 409

            print("Inserting user...")

            cur.execute(
                '''
                INSERT INTO users (
                    full_name,
                    username,
                    email,
                    phone,
                    password
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username, full_name
                ''',
                (
                    full_name,
                    username,
                    email,
                    phone,
                    generate_password_hash(password)
                )
            )

            user = cur.fetchone()

            print("Inserted User:", user)

            conn.commit()

            cur.close()
            conn.close()

        except Exception as e:

            if 'conn' in locals():
                conn.rollback()
                conn.close()

            print("REGISTER ERROR:", e)

            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']

        return jsonify({
            'success': True,
            'message': 'Registration successful'
        })

    return render_template('index.html')
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route('/api/movies')
def api_movies():
    genre = request.args.get('genre', '')
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if genre:
     cur.execute(
        "SELECT * FROM movies WHERE genre=%s ORDER BY rating DESC",
        (genre,)
    )
    else:
     cur.execute(
        "SELECT * FROM movies ORDER BY rating DESC"
    )

    movies = cur.fetchall()

    cur.close()
    conn.close()
    return jsonify(movies)

@app.route('/api/top-rated')
def api_top_rated():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
        SELECT
            m.*,
            COALESCE(AVG(r.rating), m.rating) AS avg_rating
        FROM movies m
        LEFT JOIN reviews r ON m.id = r.movie_id
        GROUP BY m.id
        ORDER BY avg_rating DESC
        LIMIT 10
    ''')

    movies = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(movies)

@app.route('/api/reviews')
def api_reviews():
    movie_id = request.args.get('movie_id', '')

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if movie_id:
        cur.execute('''
            SELECT rv.*, u.username, m.title AS movie_title
            FROM reviews rv
            JOIN users u ON rv.user_id = u.id
            JOIN movies m ON rv.movie_id = m.id
            WHERE rv.movie_id = %s
            ORDER BY rv.created_at DESC
        ''', (movie_id,))
    else:
        cur.execute('''
            SELECT rv.*, u.username, m.title AS movie_title
            FROM reviews rv
            JOIN users u ON rv.user_id = u.id
            JOIN movies m ON rv.movie_id = m.id
            ORDER BY rv.created_at DESC
        ''')

    reviews = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(reviews)

@app.route('/api/reviews/add', methods=['POST'])
def api_add_review():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    data = request.get_json()
    movie_id = data.get('movie_id')
    rating = data.get('rating')
    review_text = data.get('review_text', '')
    if not movie_id or not rating:
        return jsonify({'success': False, 'message': 'Movie and rating are required'}), 400
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id FROM reviews WHERE user_id=%s AND movie_id=%s",
        (session['user_id'], movie_id)
    )

    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': 'You already reviewed this movie'}), 409
    
    cur.execute(
        """
        INSERT INTO reviews (user_id, movie_id, rating, review_text)
        VALUES (%s, %s, %s, %s)
        """,
        (session['user_id'], movie_id, rating, review_text)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Review submitted!'})

@app.route('/api/watchlist')
def api_watchlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
    SELECT m.*
    FROM watchlist w
    JOIN movies m ON w.movie_id = m.id
    WHERE w.user_id = %s
    ORDER BY w.added_at DESC
''', (session['user_id'],))

    items = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(items)

@app.route('/api/watchlist/add', methods=['POST'])
def api_watchlist_add():
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Login required'
        }), 401

    data = request.get_json()
    movie_id = data.get('movie_id')

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO watchlist (user_id, movie_id)
            VALUES (%s, %s)
            """,
            (session['user_id'], movie_id)
        )

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Added to watchlist'
        })

    except psycopg2.Error:
        conn.rollback()

        cur.close()
        conn.close()

        return jsonify({
            'success': False,
            'message': 'Already in watchlist'
        }), 409

@app.route('/api/watchlist/remove', methods=['POST'])
def api_watchlist_remove():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    data = request.get_json()
    movie_id = data.get('movie_id')
    conn = get_db()

    cur = conn.cursor()

    cur.execute(
    """
    DELETE FROM watchlist
    WHERE user_id=%s AND movie_id=%s
    """,
    (session['user_id'], movie_id)
    )

    conn.commit()

    cur.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Removed from watchlist'})

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    webbrowser.open('http://localhost:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)