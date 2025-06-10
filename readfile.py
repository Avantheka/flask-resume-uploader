import os
import mimetypes
from tkinter import Tk, filedialog, messagebox
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client
from docx import Document
import PyPDF2


# === Step 1: Select Resume File ===
def select_file():
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select your resume",
        filetypes=(("PDF files", "*.pdf"), ("Word documents", "*.docx"), ("All files", "*.*"))
    )
    return file_path


# === Step 2: Read Resume Content ===
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
        print(f"❌ Error reading file: {e}")
        return ""
    return content.strip()


# === Step 3: Connect to WordPress and Upload ===
def connect_to_wordpress(file_path, resume_text):
    wp_url = 'https://cloudara.org/xmlrpc.php'
    wp_username = 'admin'
    wp_password = 'PAdMuHh$41ZFm'
    try:
        client = Client(wp_url, wp_username, wp_password)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        with open(file_path, 'rb') as f:
            data = {
                'name': os.path.basename(file_path),
                'type': mime_type,
                'bits': xmlrpc_client.Binary(f.read()),
                'overwrite': False
            }
            response = client.call(UploadFile(data))

        attachment_url = response['url']

        post = WordPressPost()
        post.title = "New Resume Upload"
        post.content = (
            f"A new resume has been uploaded: "
            f"<a href='{attachment_url}'>Download Resume</a><br><br>"
            f"<strong>Resume Text:</strong><pre>{resume_text}</pre>"
        )
        post.post_status = 'publish'
        client.call(NewPost(post))

        print(f"✅ Resume uploaded and published at: {attachment_url}")
    except Exception as e:
        print(f"❌ Failed to upload resume: {e}")


# === Main Program Execution ===
if __name__ == "__main__":
    file_path = select_file()
    if file_path:
        resume_text = read_resume(file_path)
        if resume_text:
            connect_to_wordpress(file_path, resume_text)
        else:
            print("❌ Could not extract text from the resume.")
    else:
        print("❌ No file selected.")
