import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, UploadForm, SearchForm, ProfileForm
from app.models import User, Post, Comment
from flask_login import login_user, current_user, logout_user, login_required

@app.context_processor
def inject_search_form():
    return dict(search_form=SearchForm())

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    form = SearchForm()
    posts = []
    if form.validate_on_submit():
        search_term = form.search.data
        search_by = 'keyword'  # Always search by keyword
        if search_by == 'keyword':
            posts = Post.query.filter(Post.keyword.contains(search_term)).order_by(Post.date_posted.desc()).all()
    elif current_user.is_authenticated:
        posts = Post.query.order_by(Post.date_posted.desc()).all()
    
    users = User.query.filter(User.id != current_user.id).all() if current_user.is_authenticated else User.query.all()
    return render_template('index.html', posts=posts, form=form, users=users)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        image_file = 'user.png'  # Default profile picture
        if form.picture.data:
            image_file = save_profile_picture(form.picture.data)
        user = User(username=form.username.data, user_id=form.user_id.data, password=hashed_password, image_file=image_file)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_id=form.user_id.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check user id and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

def save_profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    # Ensure the profile_pics directory exists
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            current_user.image_file = picture_file
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('profile'))
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', title='Profile', image_file=image_file, form=form, user_posts=current_user.posts)

@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        if form.photo.data:
            picture_file = save_picture(form.photo.data)
            post = Post(title=form.title.data, content=form.content.data, keyword=form.keyword.data, image_file=picture_file, user_id=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('home'))
    return render_template('upload.html', title='New Post', form=form)

@app.route("/post/<int:post_id>/comment", methods=['POST'])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.json.get('content')
    if content:
        comment = Comment(content=content, user_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        return jsonify({
            'id': comment.id,
            'message': 'Comment added successfully.',
            'username': current_user.username,
            'content': content
        }), 201
    return jsonify({'message': 'Comment cannot be empty.'}), 400

@app.route("/post/<int:post_id>/comments", methods=['GET'])
def get_comments(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).all()
    comments_data = [{
        'id': comment.id,
        'username': User.query.get(comment.user_id).username,
        'content': comment.content
    } for comment in comments]
    return jsonify(comments_data), 200

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    comments = Comment.query.filter_by(post_id=post.id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('profile'))

@app.route("/post/<int:post_id>")
@login_required
def get_post_details(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'title': post.title,
        'image': url_for('static', filename='uploads/' + post.image_file),
        'keyword': post.keyword,
        'content': post.content,
        'comments': [{'id': comment.id, 'username': User.query.get(comment.user_id).username, 'content': comment.content} for comment in post.comments]
    })

@app.route("/post/<int:post_id>/edit", methods=['POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    title = request.form['title']
    content = request.form['content']
    keyword = request.form['keyword']

    if 'photo' in request.files and request.files['photo'].filename != '':
        picture_file = save_picture(request.files['photo'])
        post.image_file = picture_file

    post.title = title
    post.content = content
    post.keyword = keyword

    db.session.commit()
    return jsonify({'message': 'Your post has been updated!'}), 200

@app.route("/post/<int:post_id>/comment/<int:comment_id>/delete", methods=['POST'])
@login_required
def delete_comment(post_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': '댓글이 삭제되었습니다.'}), 200

@app.route("/post/<int:post_id>/comment/<int:comment_id>/edit", methods=['POST'])
@login_required
def edit_comment(post_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        abort(403)
    content = request.json.get('content')
    if content:
        comment.content = content
        db.session.commit()
        return jsonify({'message': '댓글이 수정되었습니다.', 'content': content}), 200
    return jsonify({'message': '내용이 비어 있을 수 없습니다.'}), 400
