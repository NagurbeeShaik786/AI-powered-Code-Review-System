from flask import Flask, render_template, request, jsonify
import tempfile
import os
import logging

from code_analyzer import CodeAnalyzer

app = Flask(__name__)
analyzer = CodeAnalyzer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename='code_analyzer.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_code():
    try:
        data = request.get_json()
        code = data.get('code', '')
        language = data.get('language', 'python').lower()
        
        # Input validation
        if not code.strip():
            logging.warning("Empty code submitted")
            return jsonify({'success': False, 'error': 'No code provided'}), 400
        if len(code) > 100000:  # Limit to 100KB
            logging.warning("Code size exceeded limit")
            return jsonify({'success': False, 'error': 'Code size exceeds 100KB limit'}), 400
        if language not in ['python', 'javascript']:
            logging.warning(f"Unsupported language: {language}")
            return jsonify({'success': False, 'error': f'Unsupported language: {language}'}), 400
        
        # Analyze code
        results = analyzer.analyze(code, language)
        
        if 'error' in results:
            logging.error(f"Analysis failed: {results['error']}")
            return jsonify({'success': False, 'error': results['error']}), 500
        
        logging.info(f"Analysis completed: {results['summary']}")
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logging.error(f"Server error during analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))