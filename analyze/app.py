import os
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import asyncio

# Import your core analysis logic from analyze_data.py
# Make sure analyze_data.py is in the same directory as app.py
from analyze_data import analyze_large_file # Removed create_dummy_large_csv import as it's no longer needed in app.py

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here' # Change this to a strong, random key!
UPLOAD_FOLDER = 'uploads' # Folder where uploaded files will be stored temporarily
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Create the uploads directory if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 # 1 GB max upload size

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serves the main file upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
async def upload_file():
    """Handles the file upload and triggers analysis."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash(f'File "{filename}" successfully uploaded! Starting analysis...')

        # Define output file path for the analysis results
        analysis_output_filename = f"analysis_results_{os.path.splitext(filename)[0]}.txt"
        analysis_output_filepath = os.path.join(UPLOAD_FOLDER, analysis_output_filename)

        try:
            # Run the asynchronous analysis function in the background
            await analyze_large_file(filepath, 10000, analysis_output_filepath)
            flash(f"Analysis complete for '{filename}'. Results saved to '{analysis_output_filename}' in the 'uploads' folder.")
        except Exception as e:
            flash(f"Error during analysis of '{filename}': {e}")
            print(f"Error during analysis: {e}") # Log error to console for debugging

        return redirect(url_for('index')) # Redirect back to the upload page
    else:
        flash('Allowed file types are .csv, .xlsx')
        return redirect(request.url)

if __name__ == '__main__':
    # REMOVED: create_dummy_large_csv('large_data.csv')
    # Now you are required to upload an actual file through the web interface.

    # Run the Flask app
    # debug=True is good for development, disable in production
    app.run(debug=True, host='0.0.0.0', port=5000)

