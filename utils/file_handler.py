import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'mp4', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, course_id, module_id, upload_folder):
    if not file or not allowed_file(file.filename):
        raise ValueError("File type not allowed")

    sec_filename = secure_filename(file.filename)
    rel_dir = os.path.join(f"course_{course_id}", f"module_{module_id}")
    target_dir = os.path.join(upload_folder, rel_dir)
    
    os.makedirs(target_dir, exist_ok=True)
    abs_path = os.path.join(target_dir, sec_filename)
    file.save(abs_path)
    
    ext = sec_filename.rsplit('.', 1)[1].lower()
    return sec_filename, os.path.join(rel_dir, sec_filename), ext