from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import re

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Site Media Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
    <div class="max-w-2xl w-full p-8 bg-white rounded-3xl shadow-2xl space-y-8">
        <div class="text-center">
            <h1 class="text-3xl font-extrabold text-gray-800">Media Downloader</h1>
            <p class="mt-2 text-gray-500">Download from YouTube, Insta, FB, and more.</p>
        </div>

        <form action="/download" method="post" class="space-y-6">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input type="text" name="url" placeholder="Paste link here..." required 
                       class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none">
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
                    <select name="format" class="w-full px-4 py-3 rounded-xl border border-gray-300">
                        <option value="mp3">Audio (MP3)</option>
                        <option value="mp4">Video (MP4)</option>
                    </select>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">Start (hh:mm:ss)</label>
                        <input type="text" name="startTime" placeholder="00:00:00" class="w-full px-2 py-3 rounded-xl border border-gray-300">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">End (hh:mm:ss)</label>
                        <input type="text" name="endTime" placeholder="00:01:00" class="w-full px-2 py-3 rounded-xl border border-gray-300">
                    </div>
                </div>
            </div>

            <button type="submit" class="w-full py-3 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-all">
                Start Download
            </button>
        </form>
    </div>
</body>
</html>
"""

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename).strip().strip('.')[:200]

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    file_format = request.form.get('format')
    start_time = request.form.get('startTime')
    end_time = request.form.get('endTime')

    downloads_dir = 'downloads'
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'media_file')
            sanitized_title = sanitize_filename(video_title)

        file_path = os.path.join(downloads_dir, sanitized_title)
        
        # Base Options
        ydl_opts = {
            'outtmpl': f'{file_path}.%(ext)s',
            'noplaylist': True,
        }

        # Format Logic
        if file_format == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })
            ext = 'mp3'
        else:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })
            ext = 'mp4'

        # Clipping Logic
        if start_time and end_time:
            ydl_opts['download_sections'] = [f'*{start_time}-{end_time}']
            ydl_opts['force_keyframes_at_cuts'] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the actual file created (yt-dlp might add extra extensions during processing)
        final_file = f"{file_path}.{ext}"
        return send_file(final_file, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
