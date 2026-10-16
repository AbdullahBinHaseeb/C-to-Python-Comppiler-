import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS so the HTML file can communicate with this Python server
CORS(app) 

class CPPToPythonConverter:
    def __init__(self):
        # Lexical transformation rules
        self.rules = [
            (r'#include\s*<.*?>', ''),                      
            (r'using namespace std;', ''),                  
            (r'\bint\s+main\s*\((.*?)\)\s*\{', 'def main():'), 
            (r'\bvoid\s+(\w+)\s*\((.*?)\)\s*\{', r'def \1(\2):'), 
            (r'\bint\s+(\w+)\s*\((.*?)\)\s*\{', r'def \1(\2):'),  
            (r'std::cout\s*<<\s*(.*?);', r'print(\1)'),     
            (r'cout\s*<<\s*(.*?);', r'print(\1)'),          
            (r'std::cin\s*>>\s*(\w+);', r'\1 = input()'),   
            (r'\bfor\s*\(\s*int\s+(\w+)\s*=\s*(.*?);\s*\1\s*<\s*(.*?);\s*\1\+\+\s*\)\s*\{', r'for \1 in range(\2, \3):'), 
            (r'\bif\s*\((.*?)\)\s*\{', r'if \1:'),          
            (r'\belse\s+if\s*\((.*?)\)\s*\{', r'elif \1:'), 
            (r'\belse\s*\{', 'else:'),                      
            (r'\bwhile\s*\((.*?)\)\s*\{', r'while \1:'),    
            (r'return\s+(.*?);', r'return \1'),             
            (r'(\w+)\s*=\s*(.*?);', r'\1 = \2'),            
            (r'^\s*\}', ''),                                
            (r';', ''),                                     
        ]

    def translate(self, cpp_code):
        lines = cpp_code.split('\n')
        python_lines = []
        indent_level = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle block closures
            if line == '}':
                indent_level = max(0, indent_level - 1)
                continue
            
            translated = line
            for pattern, replacement in self.rules:
                translated = re.sub(pattern, replacement, translated)
            
            # Clean up stream operators
            translated = translated.replace('<<', ',').replace('endl', '"\\n"')
            
            # Append translated line with correct Python indentation
            if translated.strip() != "":
                python_lines.append("    " * indent_level + translated)
            
            # Increase block indentation if needed
            if '{' in line or translated.endswith(':'):
                indent_level += 1
                
        # Inject standard python execution guard if main exists
        if any('def main():' in l for l in python_lines):
            python_lines.append("")
            python_lines.append("if __name__ == '__main__':")
            python_lines.append("    main()")
            
        return "\n".join(python_lines)

@app.route('/transpile', methods=['POST'])
def transpile_api():
    try:
        # Receive JSON data from the HTML frontend
        data = request.get_json()
        cpp_code = data.get('cppCode', '')
        
        if not cpp_code:
            return jsonify({"error": "No C++ code provided"}), 400
            
        # Initialize compiler and translate
        converter = CPPToPythonConverter()
        python_result = converter.translate(cpp_code)
        
        # Send successful result back to frontend
        return jsonify({
            "status": "success",
            "pythonCode": python_result
        })
        
    except Exception as e:
        # Handle server-side parsing errors
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print(" Compiler Backend Running on http://127.0.0.1:5000")
    print("You can now open your index.html file in the browser!")
    app.run(debug=True, port=5000)6