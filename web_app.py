"""
Flask Web Application for Resume Ranking System
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import json
from pathlib import Path
import shutil

from pdf_extractor import extract_text_from_pdf
from resume_ranker import ResumeRanker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'resume-ranking-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize ranker
ranker = ResumeRanker()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and job requirements"""
    try:
        # Get job requirements
        job_requirements = request.form.get('job_requirements', '').strip()
        
        if not job_requirements:
            return jsonify({'error': 'Job requirements are required'}), 400
        
        # Get uploaded files
        if 'resumes' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('resumes')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Clear previous uploads
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        upload_dir.mkdir(exist_ok=True)
        
        # Process uploaded files
        resumes = {}
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = upload_dir / filename
                file.save(filepath)
                
                # Extract text from PDF
                text = extract_text_from_pdf(filepath)
                
                if text:
                    resumes[filename] = text
                    uploaded_files.append(filename)
        
        if not resumes:
            return jsonify({'error': 'Could not extract text from any PDF files'}), 400
        
        # Rank resumes
        results = ranker.rank_resumes(resumes, job_requirements)
        
        # Get detailed analysis for top 3 candidates
        detailed_results = []
        for i, result in enumerate(results[:3]):
            resume_text = resumes[result['filename']]
            analysis = ranker.detailed_analysis(resume_text, job_requirements)
            
            detailed_results.append({
                'rank': i + 1,
                'filename': result['filename'],
                'match_percentage': result['match_percentage'],
                'category': result['category'],
                'overall_score': analysis['overall_score'],
                'keyword_match_rate': analysis['keyword_match_rate'],
                'matching_keywords': analysis['matching_keywords'],
                'missing_keywords': analysis['missing_keywords']
            })
        
        # Prepare response
        response_data = {
            'success': True,
            'total_resumes': len(resumes),
            'job_requirements': job_requirements,
            'results': results,
            'detailed_analysis': detailed_results
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': f'Error processing resumes: {str(e)}'}), 500


@app.route('/clear-uploads', methods=['POST'])
def clear_uploads():
    """Clear uploaded files"""
    try:
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            upload_dir.mkdir(exist_ok=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Resume Ranking System - Web Application".center(60))
    print("=" * 60)
    print("\nStarting server...")
    print("\n🌐 Open your browser and go to:")
    print("   http://localhost:5000")
    print("\n   or")
    print("   http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
