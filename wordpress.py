import os
import mimetypes
from tkinter import Tk, filedialog
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client

# === Step 1: Select Resume File ===
def select_file():
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select your resume",
        filetypes=(("PDF files", "*.pdf"), ("Word documents", "*.docx"), ("All files", "*.*"))
    )
    return file_path

# === Step 2: Connect to WordPress and Upload ===
def connect_to_wordpress(file_path):
    wp_url = 'https://cloudara.org/xmlrpc.php'  # ✅ Fixed URL
    wp_username = 'admin'  # Replace with your WordPress username
    wp_password = 'PAdMuHh$41ZFm'  # Replace with your WordPress password

    client = Client(wp_url, wp_username, wp_password)

    with open(file_path, 'rb') as f:
        mime_type, _ = mimetypes.guess_type(file_path)
        data = {
            'name': os.path.basename(file_path),
            'type': mime_type or 'application/octet-stream',
            'bits': xmlrpc_client.Binary(f.read()),
            'overwrite': False
        }

    # Upload file to WordPress Media Library
    response = client.call(UploadFile(data))
    attachment_url = response['url']

    # Create a new post with the uploaded file link
    post = WordPressPost()
    post.title = "New Resume Upload"
    post.content = f"A new resume has been uploaded: <a href='{attachment_url}'>Download Resume</a>"
    post.post_status = 'publish'

    client.call(NewPost(post))
    print(f"✅ Resume uploaded and published at: {attachment_url}")

# === Main Program Execution ===
if __name__ == "__main__":
    file_path = select_file()
    if file_path:
        connect_to_wordpress(file_path)
    else:
        print("❌ No file selected.")
