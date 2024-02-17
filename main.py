from flask import Flask, render_template, request, jsonify, send_from_directory
from pytube import YouTube
import json
import os
import uuid
import requests
import random
import base64

app = Flask(__name__)

# Your GitHub personal access token
access_token = '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'

# The owner of the repository (your GitHub username or organization)
#owner = 'nitikshh'

# The name of the existing repository
repo_name = 'moviedata'


# Set up a route to serve the 'data' folder
@app.route('/data/<path:filename>')
def download_file(filename):
  return send_from_directory('data', filename)


# Set up a route to serve the 'assets' folder for static files (CSS, JS, etc.)
@app.route('/assets/<path:filename>')
def assets(filename):
  return send_from_directory('assets', filename)


@app.route('/')
def index():
  return render_template('moviz.html')


@app.route('/youtube')
def youtube():
  return render_template('youtube.html')


@app.route('/moviedetails')
def moviedetails():
  return render_template('moviedetails.html')


@app.route('/download', methods=['POST'])
def download():
  video_url = request.form['video_url']
  description = request.form['description']
  release_date = request.form['release_date']
  rating = int(request.form['rating'])
  studios = request.form['studios']
  tags = [tag.strip() for tag in request.form['tags'].split(',')]

  try:
    # Download the video
    yt = YouTube(video_url)
    video_stream = yt.streams.get_highest_resolution()

    # Generate unique filename using UUID
    unique_filename = f"{str(uuid.uuid4())}"

    # Save video to the "data/videos" folder with the same name
    video_filename = f"{unique_filename}.mp4"
    video_path = os.path.join('data/videos', video_filename)
    video_stream.download('data/videos', filename=video_filename)

    # Save thumbnail to the "data/videos" folder with the same name
    thumbnail_filename = f"{unique_filename}.jpg"
    thumbnail_url = yt.thumbnail_url
    thumbnail_data = requests.get(thumbnail_url).content
    thumbnail_path = os.path.join('data/videos', thumbnail_filename)
    with open(thumbnail_path, 'wb') as thumbnail_file:
      thumbnail_file.write(thumbnail_data)

    # Save video to GitHub
    github_video_url = upload_video_to_github(video_path, unique_filename)

    # Save thumbnail to GitHub
    github_thumbnail_url = upload_thumbnail_to_github(thumbnail_data,
                                                      unique_filename)

    github_image_url = "https://nitikshh.github.io/moviedata/data/images/" + thumbnail_filename
    github_video_url = "https://nitikshh.github.io/moviedata/data/videos/" + video_filename

    # Generate a unique ID using UUID
    unique_id = str(uuid.uuid4())

    # Save information to data/json/data.json
    data = {
        'id': unique_id,
        'title': yt.title,
        'thumbnail': github_image_url,
        'video_path': github_video_url,
        'duration': yt.length,
        'type': 'movie',
        'description': description,
        'release_date': release_date,
        'rating': rating,
        'studios': studios,
        'tags': tags,
    }
    save_to_json(data)

    return jsonify({
        'success': True,
        'message': 'Video downloaded successfully.',
        'id': unique_id,
        'github_thumbnail_url': github_thumbnail_url
    })
  except Exception as e:
    return jsonify({'success': False, 'message': f'Error: {str(e)}'})


def save_to_json(data):
  json_path = 'data/json/data.json'

  if os.path.exists(json_path):
    with open(json_path, 'r') as json_file:
      try:
        existing_data = json.load(json_file)
      except json.JSONDecodeError:
        existing_data = []
  else:
    existing_data = []

  existing_data.append(data)

  with open(json_path, 'w') as json_file:
    json.dump(existing_data, json_file, indent=2)


def upload_video_to_github(video_path, unique_filename):
  try:
    # Read the video content
    with open(video_path, 'rb') as video_file:
      video_content = video_file.read()

    # Encode the video content to Base64
    video_content_base64 = base64.b64encode(video_content).decode()

    # Add the video to the GitHub repository
    url = f'https://api.github.com/repos/{owner}/{repo_name}/contents/data/videos/{unique_filename}.mp4'
    headers = {'Authorization': f'token {access_token}'}

    payload = {
        'message': 'Upload video',
        'content': video_content_base64,
        'branch': 'main'  # Specify the branch you want to commit to
    }

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 201:
      github_video_url = f'https://raw.githubusercontent.com/{owner}/{repo_name}/main/data/videos/{unique_filename}.mp4'
      return github_video_url
    else:
      raise Exception(
          f'Failed to upload video to GitHub. Status code: {response.status_code}'
      )

  except Exception as e:
    raise Exception(f'Error uploading video to GitHub: {str(e)}')


def upload_thumbnail_to_github(thumbnail_data, unique_filename):
  try:
    # Encode the thumbnail content to Base64
    thumbnail_content = base64.b64encode(thumbnail_data).decode()

    # Add the thumbnail to the GitHub repository
    url = f'https://api.github.com/repos/{owner}/{repo_name}/contents/data/images/{unique_filename}.jpg'
    headers = {'Authorization': f'token {access_token}'}

    payload = {
        'message': 'Upload thumbnail',
        'content': thumbnail_content,
        'branch': 'main'  # Specify the branch you want to commit to
    }

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 201:
      github_thumbnail_url = f'https://raw.githubusercontent.com/{owner}/{repo_name}/main/data/images/{unique_filename}.jpg'
      return github_thumbnail_url
    else:
      raise Exception(
          f'Failed to upload thumbnail to GitHub. Status code: {response.status_code}'
      )

  except Exception as e:
    raise Exception(f'Error uploading thumbnail to GitHub: {str(e)}')


@app.route('/subscribe', methods=['POST'])
def subscribe():
  email = request.form['email']

  try:
    # Save the email to data/emails/emails.json
    save_email_to_json(email)

    return jsonify({
        'success': True,
        'message': 'Email subscribed successfully.',
        'reload': True  # Add this key to indicate a reload
    })

  except Exception as e:
    return jsonify({'success': False, 'message': f'Error: {str(e)}'})


def save_email_to_json(email):
  json_path = 'data/emails/emails.json'

  if os.path.exists(json_path):
    with open(json_path, 'r') as json_file:
      try:
        existing_emails = json.load(json_file)
      except json.JSONDecodeError:
        existing_emails = []
  else:
    existing_emails = []

  existing_emails.append({'email': email})

  with open(json_path, 'w') as json_file:
    json.dump(existing_emails, json_file, indent=2)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=random.randint(2000, 9000), debug=True)
