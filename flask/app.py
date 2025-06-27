#!/usr/bin/env python3
from flask import Flask, render_template_string, request, send_file, redirect, url_for
import os
import tempfile
import yt_dlp
import uuid

app = Flask(__name__)

# HTML Template with embedded CSS and JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #ff0000;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="url"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        .radio-group {
            margin: 15px 0;
        }
        .radio-group label {
            display: inline-block;
            margin-right: 15px;
            font-weight: normal;
            cursor: pointer;
        }
        button {
            background-color: #ff0000;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #cc0000;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top: 4px solid #ff0000;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            color: #ff0000;
            margin-top: 10px;
        }
        .success {
            color: #28a745;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Downloader</h1>
        <form id="downloadForm" onsubmit="return submitForm()">
            <div class="form-group">
                <label for="youtube_url">YouTube URL:</label>
                <input type="url" id="youtube_url" name="youtube_url" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            
            <div class="radio-group">
                <label>
                    <input type="radio" name="format" value="mp4" checked> MP4 (Video)
                </label>
                <label>
                    <input type="radio" name="format" value="mp3"> MP3 (Audio)
                </label>
            </div>
            
            <button type="submit">Download</button>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Processing your request, please wait...</p>
            </div>
            
            <div id="message"></div>
        </form>
    </div>

    <script>
        function submitForm() {
            const form = document.getElementById('downloadForm');
            const loading = document.getElementById('loading');
            const message = document.getElementById('message');
            
            // Show loading spinner
            loading.style.display = 'block';
            message.innerHTML = '';
            message.className = '';
            
            // Get form data
            const formData = new FormData(form);
            const url = formData.get('youtube_url');
            const format = formData.get('format');
            
            // Send to server
            fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `youtube_url=${encodeURIComponent(url)}&format=${format}`
            })
            .then(response => {
                loading.style.display = 'none';
                if (response.redirected) {
                    // If server redirected to download, trigger the download
                    window.location.href = response.url;
                } else {
                    return response.json();
                }
            })
            .then(data => {
                if (data && data.error) {
                    message.innerHTML = data.error;
                    message.className = 'error';
                } else if (data && data.success) {
                    message.innerHTML = data.success;
                    message.className = 'success';
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                message.innerHTML = 'An error occurred: ' + error;
                message.className = 'error';
            });
            
            return false; // Prevent default form submission
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

def download_video(url, format):
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4().hex
    filename = f"youtube_download_{unique_id}"
    
    if format == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(temp_dir, filename + '.%(ext)s'),
            'quiet': True,
        }
        ext = 'mp3'
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(temp_dir, filename + '.%(ext)s'),
            'quiet': True,
        }
        ext = 'mp4'
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)
    
    if format == 'mp3':
        final_filename = f"{filename}.{ext}"
        final_path = os.path.join(temp_dir, final_filename)
        if not os.path.exists(final_path):
            # Sometimes the extension might be different (m4a, etc.)
            for f in os.listdir(temp_dir):
                if f.startswith(filename):
                    final_path = os.path.join(temp_dir, f)
                    break
        return final_path
    else:
        return downloaded_file

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('youtube_url')
    format = request.form.get('format', 'mp4')
    
    if not url:
        return {'error': 'Please provide a YouTube URL'}, 400
    
    try:
        # First get video info to validate URL
        video_info = get_video_info(url)
        if not video_info:
            return {'error': 'Could not retrieve video information. Please check the URL.'}, 400
        
        # Download the file
        file_path = download_video(url, format)
        
        if not os.path.exists(file_path):
            return {'error': 'File could not be downloaded. Please try again.'}, 500
        
        # Determine the filename for download
        title = video_info.get('title', 'video')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        download_filename = f"{safe_title}.{format}"
        
        # Return the file for download
        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype=f'audio/mpeg' if format == 'mp3' else 'video/mp4'
        )
        
    except yt_dlp.utils.DownloadError as e:
        return {'error': f'Download error: {str(e)}'}, 400
    except Exception as e:
        return {'error': f'An error occurred: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(debug=True)
