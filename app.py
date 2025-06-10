import os
from flask import Flask, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client
from docx import Document
import PyPDF2

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Check if the file type is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Extract text content from resume
def read_resume(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    content = ""

    try:
        if ext == ".pdf":
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    content += page.extract_text() or ""
        elif ext == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                content += para.text + "\n"
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

    return content.strip()


# --- Upload route (GET for form, POST for upload)
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['resume']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        resume_text = read_resume(file_path)

        try:
            # === WordPress XML-RPC connection ===
            wp_url = 'https://cloudara.org/xmlrpc.php'
            wp_username = 'admin'
            wp_password = 'PAdMuHh$41ZFm'

            client = Client(wp_url, wp_username, wp_password)

            # === Upload file to WordPress ===
            with open(file_path, 'rb') as f:
                data = {
                    'name': filename,
                    'type': 'application/octet-stream',
                    'bits': xmlrpc_client.Binary(f.read()),
                    'overwrite': False
                }

                response = client.call(UploadFile(data))
                attachment_url = response['url']

            # === Create and publish post ===
            post = WordPressPost()
            post.title = "New Resume Upload"
            post.content = (
                f"A new resume has been uploaded: "
                f"<a href='{attachment_url}'>Download Resume</a><br><br>"
                f"<strong>Resume Text:</strong><br><pre>{resume_text}</pre>"
            )
            post.post_status = 'publish'
            client.call(NewPost(post))

            return f'''
                <h3>✅ Resume uploaded successfully!</h3>
                <p>View it on WordPress: <a href="{attachment_url}" target="_blank">{attachment_url}</a></p>
                <hr>
                <h4>Extracted Resume Content:</h4>
                <pre>{resume_text}</pre>
            '''

        except Exception as e:
            return f"<p><strong>❌ WordPress Error:</strong> {str(e)}</p>", 500

    # === GET request: display file upload form
    return '''
    <h2>Upload Your Resume</h2>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="resume" required><br><br>
        <input type="submit" value="Upload">
    </form>
    <p>Accepted file types: PDF, DOCX, TXT</p>
    '''


# --- Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
