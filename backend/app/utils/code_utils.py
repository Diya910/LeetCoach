"""
Code analysis and processing utilities.
"""

import re
import ast
from typing import Dict, Any, Optional, List
from ..models.request_models import ProgrammingLanguage


class LanguageDetector:
    """Detect programming language from code snippets."""
    
    # Language-specific patterns
    LANGUAGE_PATTERNS = {
        ProgrammingLanguage.PYTHON: [
            r'def\s+\w+\s*\(',  # function definition
            r'import\s+\w+',    # import statement
            r'from\s+\w+\s+import',  # from import
            r'if\s+__name__\s*==\s*["\']__main__["\']',  # main guard
            r':\s*$',  # colon at end of line (indentation-based)
        ],
        ProgrammingLanguage.JAVA: [
            r'public\s+class\s+\w+',  # class declaration
            r'public\s+static\s+void\s+main',  # main method
            r'System\.out\.print',  # print statement
            r'import\s+java\.',  # java import
            r'\w+\s+\w+\s*\([^)]*\)\s*\{',  # method with braces
        ],
        ProgrammingLanguage.CPP: [
            r'#include\s*<[^>]+>',  # include statement
            r'std::\w+',  # std namespace
            r'cout\s*<<',  # cout statement
            r'int\s+main\s*\(',  # main function
            r'\w+\s*::\s*\w+',  # scope resolution
        ],
        ProgrammingLanguage.JAVASCRIPT: [
            r'function\s+\w+\s*\(',  # function declaration
            r'const\s+\w+\s*=',  # const declaration
            r'let\s+\w+\s*=',  # let declaration
            r'console\.log',  # console.log
            r'=>\s*\{',  # arrow function
        ],
        ProgrammingLanguage.TYPESCRIPT: [
            r':\s*\w+\s*=',  # type annotation
            r'interface\s+\w+',  # interface declaration
            r'type\s+\w+\s*=',  # type alias
            r'function\s+\w+\s*\([^)]*\)\s*:\s*\w+',  # typed function
        ],
        ProgrammingLanguage.CSHARP: [
            r'using\s+System',  # using statement
            r'public\s+class\s+\w+',  # class declaration
            r'Console\.WriteLine',  # console output
            r'static\s+void\s+Main',  # main method
        ],
        ProgrammingLanguage.GO: [
            r'package\s+\w+',  # package declaration
            r'import\s*\(',  # import block
            r'func\s+\w+\s*\(',  # function declaration
            r'fmt\.Print',  # fmt package
        ],
        ProgrammingLanguage.RUST: [
            r'fn\s+\w+\s*\(',  # function declaration
            r'let\s+mut\s+\w+',  # mutable variable
            r'println!',  # println macro
            r'use\s+std::\w+',  # use statement
        ]
    }
    
    @classmethod
    def detect_language(cls, code: str) -> Optional[ProgrammingLanguage]:
        """
        Detect programming language from code snippet.
        
        Args:
            code: Code snippet to analyze
            
        Returns:
            Detected programming language or None if uncertain
        """
        scores = {}
        
        for language, patterns in cls.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, code, re.MULTILINE | re.IGNORECASE))
                score += matches
            scores[language] = score
        
        # Return language with highest score, or None if no clear winner
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return None


class CodeAnalyzer:
    """Analyze code structure and extract information."""
    
    @staticmethod
    def extract_functions(code: str, language: ProgrammingLanguage) -> List[Dict[str, Any]]:
        """
        Extract function definitions from code.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            List of function information dictionaries
        """
        functions = []
        
        if language == ProgrammingLanguage.PYTHON:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append({
                            'name': node.name,
                            'line_number': node.lineno,
                            'args': [arg.arg for arg in node.args.args],
                            'docstring': ast.get_docstring(node)
                        })
            except SyntaxError:
                pass  # Handle malformed code gracefully
        
        elif language == ProgrammingLanguage.JAVA:
            # Java method pattern
            pattern = r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*\{'
            matches = re.finditer(pattern, code)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    'name': match.group(1),
                    'line_number': line_number,
                    'signature': match.group(0)
                })
        
        elif language == ProgrammingLanguage.JAVASCRIPT:
            # JavaScript function patterns
            patterns = [
                r'function\s+(\w+)\s*\([^)]*\)',  # function declaration
                r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',  # arrow function
                r'(\w+)\s*:\s*function\s*\([^)]*\)'  # method in object
            ]
            for pattern in patterns:
                matches = re.finditer(pattern, code)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    functions.append({
                        'name': match.group(1),
                        'line_number': line_number,
                        'signature': match.group(0)
                    })
        
        return functions
    
    @staticmethod
    def count_lines_of_code(code: str) -> Dict[str, int]:
        """
        Count different types of lines in code.
        
        Args:
            code: Source code
            
        Returns:
            Dictionary with line counts
        """
        lines = code.split('\n')
        
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = 0
        
        # Count comment lines (basic patterns)
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('#') or  # Python, shell
                stripped.startswith('//') or  # C++, Java, JS
                stripped.startswith('/*') or stripped.startswith('*')):  # Multi-line comments
                comment_lines += 1
        
        code_lines = total_lines - blank_lines - comment_lines
        
        return {
            'total': total_lines,
            'code': code_lines,
            'blank': blank_lines,
            'comment': comment_lines
        }
    
    @staticmethod
    def extract_imports(code: str, language: ProgrammingLanguage) -> List[str]:
        """
        Extract import statements from code.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            List of import statements
        """
        imports = []
        
        if language == ProgrammingLanguage.PYTHON:
            patterns = [
                r'import\s+([^\s]+)',
                r'from\s+([^\s]+)\s+import'
            ]
        elif language == ProgrammingLanguage.JAVA:
            patterns = [r'import\s+([^;]+);']
        elif language == ProgrammingLanguage.JAVASCRIPT:
            patterns = [
                r'import\s+.*from\s+["\']([^"\']+)["\']',
                r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
            ]
        elif language == ProgrammingLanguage.CPP:
            patterns = [r'#include\s*[<"]([^>"]+)[>"]']
        else:
            patterns = []
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            imports.extend(matches)
        
        return imports
    
    @staticmethod
    def find_potential_issues(code: str, language: ProgrammingLanguage) -> List[Dict[str, Any]]:
        """
        Find potential issues in code (basic static analysis).
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            List of potential issues
        """
        issues = []
        lines = code.split('\n')
        
        # Common issues across languages
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append({
                    'type': 'style',
                    'line': i,
                    'message': 'Line too long (>120 characters)',
                    'severity': 'warning'
                })
            
            # TODO/FIXME comments
            if re.search(r'(TODO|FIXME|HACK)', line, re.IGNORECASE):
                issues.append({
                    'type': 'maintenance',
                    'line': i,
                    'message': 'TODO/FIXME comment found',
                    'severity': 'info'
                })
        
        # Language-specific checks
        if language == ProgrammingLanguage.PYTHON:
            # Check for common Python issues
            for i, line in enumerate(lines, 1):
                if re.search(r'print\s*\(', line) and 'debug' not in line.lower():
                    issues.append({
                        'type': 'debug',
                        'line': i,
                        'message': 'Print statement found (possible debug code)',
                        'severity': 'warning'
                    })
        
        return issues
    
    @staticmethod
    def format_code_block(code: str, language: ProgrammingLanguage) -> str:
        """
        Format code block for display.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Formatted code block
        """
        lang_map = {
            ProgrammingLanguage.PYTHON: 'python',
            ProgrammingLanguage.JAVA: 'java',
            ProgrammingLanguage.JAVASCRIPT: 'javascript',
            ProgrammingLanguage.TYPESCRIPT: 'typescript',
            ProgrammingLanguage.CPP: 'cpp',
            ProgrammingLanguage.C: 'c',
            ProgrammingLanguage.CSHARP: 'csharp',
            ProgrammingLanguage.GO: 'go',
            ProgrammingLanguage.RUST: 'rust'
        }
        
        lang_str = lang_map.get(language, 'text')
        return f"```{lang_str}\n{code}\n```"
