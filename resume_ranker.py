"""
Resume Ranking System
Ranks resumes based on job requirements using semantic similarity
"""

import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


class ResumeRanker:
    """
    Resume ranking system that matches resumes to job requirements
    """
    
    def __init__(self, model_path='resume_model.pkl', encoder_path='label_encoder.pkl'):
        """
        Initialize the ranker with trained model and embeddings
        
        Args:
            model_path: Path to trained classification model
            encoder_path: Path to label encoder
        """
        # Load SBERT model for embeddings
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load trained model and all feature transformers
        try:
            with open(model_path, 'rb') as f:
                self.classifier = pickle.load(f)
            with open(encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            with open('tfidf_vectorizer.pkl', 'rb') as f:
                self.tfidf = pickle.load(f)
            with open('char_vectorizer.pkl', 'rb') as f:
                self.char_vectorizer = pickle.load(f)
            with open('feature_scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            with open('feature_selector.pkl', 'rb') as f:
                self.selector = pickle.load(f)
            self.model_loaded = True
        except Exception as e:
            print(f"Warning: Could not load trained model: {e}. Category prediction disabled.")
            self.model_loaded = False
    
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\+?\d[\d\s\-\(\)]{7,}\d', '', text)
        text = re.sub(r'[^\w\s\+\#\-\.]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    
    def extract_features(self, resume_text):
        """
        Extract all features from resume text (same as training pipeline)
        
        Args:
            resume_text: Resume text content
            
        Returns:
            Feature array ready for model prediction
        """
        # Clean text
        clean = self.clean_text(resume_text)
        
        # 1. SBERT embeddings (384 dims)
        embeddings = self.sbert_model.encode([clean])
        
        # 2. TF-IDF features (100 dims)
        tfidf_features = self.tfidf.transform([clean]).toarray()
        
        # 3. Character n-grams (50 dims)
        char_ngrams = self.char_vectorizer.transform([clean]).toarray()
        
        # 4. Statistical features (36 dims)
        # Text length features
        text_length = len(clean)
        words = clean.split()
        word_count = len(words)
        avg_word_length = np.mean([len(w) for w in words]) if words else 0
        unique_word_count = len(set(words))
        lexical_diversity = unique_word_count / (word_count + 1)
        
        # Sentence features
        sentences = re.split(r'[.!?]+', clean)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / (sentence_count + 1)
        
        # Special character counts
        number_count = len(re.findall(r'\d', clean))
        uppercase_count = sum(1 for c in resume_text if c.isupper())
        
        # Normalized features
        caps_ratio = sum(1 for c in clean if c.isupper()) / max(len(clean), 1)
        digit_ratio = sum(1 for c in clean if c.isdigit()) / max(len(clean), 1)
        special_char_ratio = sum(1 for c in clean if not c.isalnum() and not c.isspace()) / max(len(clean), 1)
        punctuation_density = (clean.count('.') + clean.count(',') + clean.count(';')) / max(len(words), 1)
        readability_score = avg_word_length / 10.0
        
        # Technical skills
        technical_skills = {
            'programming_languages': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'go', 'rust', 'scala', 'kotlin', 'swift', 'r', 'matlab'],
            'web_frameworks': ['django', 'flask', 'react', 'angular', 'vue', 'spring', 'node.js', 'express', 'asp.net', 'laravel'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'cassandra', 'dynamodb', 'sqlite'],
            'cloud_platforms': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins'],
            'data_science': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy', 'scikit-learn', 'nlp'],
            'tools': ['git', 'jira', 'linux', 'agile', 'scrum', 'ci/cd', 'devops']
        }
        
        skill_counts = []
        for skills in technical_skills.values():
            count = sum(1 for skill in skills if skill in clean.lower())
            skill_counts.append(count)
        total_tech_skills = sum(skill_counts)
        skill_counts.append(total_tech_skills)
        
        # Experience & education
        years_mentioned = len(re.findall(r'\d+\s*(?:year|yr)', clean, re.IGNORECASE))
        experience_level = (
            ('senior' in clean.lower()) * 2 +
            ('lead' in clean.lower()) * 2 +
            ('principal' in clean.lower()) * 3 +
            ('architect' in clean.lower()) * 2 +
            ('junior' in clean.lower()) * -1
        )
        has_phd = int(bool(re.search(r'\bphd\b|\bdoctorate\b', clean, re.IGNORECASE)))
        has_masters = int(bool(re.search(r'\bmaster|\bmsc\b|\bms\b', clean, re.IGNORECASE)))
        has_bachelors = int(bool(re.search(r'\bbachelor|\bbsc\b|\bbs\b|\bba\b', clean, re.IGNORECASE)))
        has_certifications = sum([
            'certified' in clean.lower(),
            'certification' in clean.lower(),
            'aws certified' in clean.lower(),
            'pmp' in clean.lower(),
            'cissp' in clean.lower()
        ])
        project_count = len(re.findall(r'\bproject\b', clean, re.IGNORECASE))
        
        # Domain keywords
        domain_keywords = {
            'management': ['team', 'lead', 'manager', 'coordinate', 'supervise', 'budget', 'stakeholder'],
            'development': ['develop', 'build', 'implement', 'code', 'programming', 'software', 'application'],
            'data_analytics': ['analysis', 'analytics', 'data', 'statistics', 'visualization', 'insights', 'reporting'],
            'design': ['design', 'ui', 'ux', 'interface', 'wireframe', 'prototype', 'figma', 'sketch'],
            'testing': ['test', 'qa', 'quality', 'automation', 'selenium', 'bug', 'defect'],
            'security': ['security', 'firewall', 'encryption', 'vulnerability', 'penetration', 'network'],
            'devops': ['deployment', 'ci/cd', 'pipeline', 'automation', 'infrastructure', 'monitoring'],
            'sales_marketing': ['sales', 'marketing', 'customer', 'revenue', 'campaign', 'roi', 'conversion']
        }
        
        domain_counts = []
        for keywords in domain_keywords.values():
            count = sum(1 for kw in keywords if kw in clean.lower())
            domain_counts.append(count)
        
        # Combine all statistical features (36 total)
        statistical_features = np.array([[
            text_length, word_count, avg_word_length, unique_word_count, lexical_diversity,
            sentence_count, avg_sentence_length, number_count, uppercase_count,
            caps_ratio, digit_ratio, special_char_ratio, punctuation_density, readability_score,
            *skill_counts,
            years_mentioned, experience_level, has_phd, has_masters, has_bachelors,
            has_certifications, project_count,
            *domain_counts
        ]])
        
        # Scale statistical features
        statistical_features_scaled = self.scaler.transform(statistical_features)
        
        # Combine all features (570 dims total)
        combined_features = np.hstack([
            embeddings,
            tfidf_features,
            char_ngrams,
            statistical_features_scaled
        ])
        
        # Apply feature selection (570 → 300)
        X_selected = self.selector.transform(combined_features)
        
        return X_selected
    
    
    def predict_category(self, resume_text):
        """
        Predict the job category of a resume
        
        Args:
            resume_text: Resume text content
            
        Returns:
            Predicted category name
        """
        if not self.model_loaded:
            return "Unknown"
        
        # Extract all features
        features = self.extract_features(resume_text)
        
        # Predict
        prediction = self.classifier.predict(features)[0]
        category = self.label_encoder.inverse_transform([prediction])[0]
        
        return category
    
    
    def calculate_similarity(self, resume_text, job_requirements):
        """
        Calculate semantic similarity between resume and job requirements
        
        Args:
            resume_text: Resume text content
            job_requirements: Job requirements text
            
        Returns:
            Similarity score (0-1)
        """
        # Clean texts
        resume_clean = self.clean_text(resume_text)
        job_clean = self.clean_text(job_requirements)
        
        # Generate embeddings
        resume_embedding = self.sbert_model.encode([resume_clean])
        job_embedding = self.sbert_model.encode([job_clean])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(resume_embedding, job_embedding)[0][0]
        
        return float(similarity)
    
    
    def rank_resumes(self, resumes, job_requirements, top_n=None):
        """
        Rank multiple resumes based on job requirements
        
        Args:
            resumes: Dictionary with {filename: resume_text}
            job_requirements: Job requirements text
            top_n: Number of top resumes to return (None = all)
            
        Returns:
            List of tuples (filename, score, category) sorted by score
        """
        results = []
        
        for filename, resume_text in resumes.items():
            # Calculate similarity score
            score = self.calculate_similarity(resume_text, job_requirements)
            
            # Predict category
            category = self.predict_category(resume_text)
            
            results.append({
                'filename': filename,
                'score': score,
                'category': category,
                'match_percentage': round(score * 100, 2)
            })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N if specified
        if top_n:
            results = results[:top_n]
        
        return results
    
    
    def extract_keywords(self, text):
        """
        Extract important keywords from text
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Common technical keywords
        keywords = {
            'languages': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala'],
            'frameworks': ['django', 'flask', 'react', 'angular', 'vue', 'spring', 'node.js', 'express'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'data_science': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy'],
            'tools': ['git', 'jira', 'linux', 'agile', 'ci/cd']
        }
        
        text_lower = text.lower()
        found_keywords = []
        
        for category, terms in keywords.items():
            for term in terms:
                if term in text_lower:
                    found_keywords.append(term)
        
        return list(set(found_keywords))
    
    
    def detailed_analysis(self, resume_text, job_requirements):
        """
        Provide detailed analysis of resume vs job requirements
        
        Args:
            resume_text: Resume text
            job_requirements: Job requirements text
            
        Returns:
            Dictionary with detailed analysis
        """
        # Calculate similarity
        score = self.calculate_similarity(resume_text, job_requirements)
        
        # Extract keywords
        resume_keywords = self.extract_keywords(resume_text)
        job_keywords = self.extract_keywords(job_requirements)
        
        # Find matching and missing keywords
        matching_keywords = set(resume_keywords) & set(job_keywords)
        missing_keywords = set(job_keywords) - set(resume_keywords)
        
        # Predict category
        category = self.predict_category(resume_text)
        
        return {
            'overall_score': round(score * 100, 2),
            'predicted_category': category,
            'matching_keywords': list(matching_keywords),
            'missing_keywords': list(missing_keywords),
            'keyword_match_rate': round(len(matching_keywords) / len(job_keywords) * 100, 2) if job_keywords else 0
        }
