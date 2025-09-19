import tempfile
import os
import subprocess
import json
import re
import shutil
import logging
from typing import Dict, List, Any

class CodeAnalyzer:
    def __init__(self):
        self.python_analyzers = ['pylint', 'flake8']
        # Check tool availability
        for tool in self.python_analyzers:
            if not shutil.which(tool):
                logging.error(f"{tool} is not installed. Please install it using 'pip install {tool}'.")
        if not shutil.which('eslint'):
            logging.warning("ESLint is not installed. JavaScript analysis will be limited.")

    def analyze(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code and return bugs, warnings, and suggestions"""
        language = language.lower()
        if language == 'python':
            return self._analyze_python(code)
        elif language == 'javascript':
            return self._analyze_javascript(code)
        else:
            logging.warning(f"Unsupported language: {language}")
            return {
                'bugs': [],
                'warnings': [],
                'suggestions': [],
                'error': f'Language "{language}" is not supported. Supported languages: python, javascript'
            }

    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyze Python code using pylint and flake8"""
        bugs = []
        warnings = []
        suggestions = []
        temp_file = None

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Run pylint
            pylint_results = self._run_pylint(temp_file)
            if 'error' in pylint_results:
                return pylint_results
            bugs.extend(pylint_results['bugs'])
            warnings.extend(pylint_results['warnings'])
            suggestions.extend(pylint_results['suggestions'])

            # Run flake8
            flake8_results = self._run_flake8(temp_file)
            if 'error' in flake8_results:
                return flake8_results
            bugs.extend(flake8_results['bugs'])
            warnings.extend(flake8_results['warnings'])

        except Exception as e:
            logging.error(f"Python analysis failed: {str(e)}")
            return {
                'bugs': [],
                'warnings': [],
                'suggestions': [],
                'error': f'Python analysis failed: {str(e)}'
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError as e:
                    logging.error(f"Failed to delete temporary file {temp_file}: {str(e)}")

        return {
            'bugs': bugs,
            'warnings': warnings,
            'suggestions': suggestions,
            'summary': f'Found {len(bugs)} bugs, {len(warnings)} warnings, {len(suggestions)} suggestions'
        }

    def _run_pylint(self, file_path: str) -> Dict[str, List]:
        """Run pylint and parse results"""
        bugs = []
        warnings = []
        suggestions = []

        if not shutil.which('pylint'):
            logging.error("pylint not found")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'pylint not installed. Install using "pip install pylint".'}

        try:
            result = subprocess.run(
                ['pylint', '--output-format=json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.stdout:
                pylint_output = json.loads(result.stdout)
                for issue in pylint_output:
                    item = {
                        'line': issue.get('line', 0),
                        'column': issue.get('column', 0),
                        'message': issue.get('message', ''),
                        'type': issue.get('type', ''),
                        'symbol': issue.get('symbol', '')
                    }
                    if issue.get('type') == 'error':
                        bugs.append(item)
                    elif issue.get('type') == 'warning':
                        warnings.append(item)
                    elif issue.get('type') in ['convention', 'refactor']:
                        suggestions.append(item)
            else:
                logging.error(f"pylint failed with stderr: {result.stderr}")
                return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': f'pylint failed: {result.stderr}'}

        except subprocess.TimeoutExpired:
            logging.error("pylint timed out after 30 seconds")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'pylint analysis timed out'}
        except json.JSONDecodeError as e:
            logging.error(f"pylint JSON parsing failed: {str(e)}")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'Failed to parse pylint output'}
        except Exception as e:
            logging.error(f"pylint error: {str(e)}")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': f'pylint error: {str(e)}'}

        return {'bugs': bugs, 'warnings': warnings, 'suggestions': suggestions}

    def _run_flake8(self, file_path: str) -> Dict[str, List]:
        """Run flake8 and parse results"""
        bugs = []
        warnings = []

        if not shutil.which('flake8'):
            logging.error("flake8 not found")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'flake8 not installed. Install using "pip install flake8".'}

        try:
            result = subprocess.run(
                ['flake8', '--format=%(row)d:%(col)d:%(code)s:%(text)s', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        item = {
                            'line': int(parts[0]),
                            'column': int(parts[1]),
                            'code': parts[2],
                            'message': parts[3],
                            'type': 'style'
                        }
                        if parts[2].startswith('E'):
                            bugs.append(item)
                        else:
                            warnings.append(item)
        except subprocess.TimeoutExpired:
            logging.error("flake8 timed out after 30 seconds")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'flake8 analysis timed out'}
        except Exception as e:
            logging.error(f"flake8 error: {str(e)}")
            return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': f'flake8 error: {str(e)}'}

        return {'bugs': bugs, 'warnings': warnings}

    def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code using ESLint or fallback to regex"""
        bugs = []
        warnings = []
        suggestions = []
        temp_file = None

        if shutil.which('eslint'):
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    f.write(code)
                    temp_file = f.name

                # Run ESLint
                result = subprocess.run(
                    ['eslint', '--format=json', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    eslint_output = json.loads(result.stdout)
                    for file in eslint_output:
                        for issue in file.get('messages', []):
                            item = {
                                'line': issue.get('line', 0),
                                'column': issue.get('column', 0),
                                'message': issue.get('message', ''),
                                'type': issue.get('severity', 1) == 2 and 'error' or 'warning',
                                'symbol': issue.get('ruleId', '')
                            }
                            if issue.get('severity') == 2:
                                bugs.append(item)
                            else:
                                warnings.append(item)
                else:
                    logging.error(f"ESLint failed with stderr: {result.stderr}")
                    return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': f'ESLint failed: {result.stderr}'}
            except subprocess.TimeoutExpired:
                logging.error("ESLint timed out after 30 seconds")
                return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'ESLint analysis timed out'}
            except json.JSONDecodeError as e:
                logging.error(f"ESLint JSON parsing failed: {str(e)}")
                return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': 'Failed to parse ESLint output'}
            except Exception as e:
                logging.error(f"ESLint error: {str(e)}")
                return {'bugs': [], 'warnings': [], 'suggestions': [], 'error': f'ESLint error: {str(e)}'}
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except OSError as e:
                        logging.error(f"Failed to delete temporary file {temp_file}: {str(e)}")
        else:
            # Fallback to regex-based analysis
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(r'[^;{}]\s*$', line.strip()) and line.strip() and not line.strip().endswith('{') and not line.strip().endswith('}'):
                    if not re.match(r'^\s*(if|for|while|function|else|try|catch|finally)', line.strip()):
                        suggestions.append({
                            'line': i,
                            'message': 'Consider adding semicolon at end of statement',
                            'type': 'style'
                        })
                if re.search(r'\bvar\s+', line):
                    suggestions.append({
                        'line': i,
                        'message': 'Consider using let or const instead of var',
                        'type': 'modern'
                    })
                if re.search(r'console\.log', line):
                    warnings.append({
                        'line': i,
                        'message': 'Remove console.log statements in production code',
                        'type': 'warning'
                    })
                if re.search(r'==(?!=)', line):
                    suggestions.append({
                        'line': i,
                        'message': 'Use strict equality (===) instead of loose equality (==)',
                        'type': 'best_practice'
                    })
                if re.search(r'function\s*\(\s*\)', line):
                    suggestions.append({
                        'line': i,
                        'message': 'Consider using arrow functions for better readability',
                        'type': 'modern'
                    })

        return {
            'bugs': bugs,
            'warnings': warnings,
            'suggestions': suggestions,
            'summary': f'Found {len(bugs)} bugs, {len(warnings)} warnings, {len(suggestions)} suggestions'
        }