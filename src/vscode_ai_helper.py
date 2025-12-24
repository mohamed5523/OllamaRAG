#!/usr/bin/env python3
"""
VS Code AI Helper Script
This script helps integrate selected code with the AI CLI
Usage: python vscode_ai_helper.py <command> <server_ip> [file_path]
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

def get_selected_text():
    """
    Read selected text from stdin (piped from VS Code)
    """
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None

def detect_language_from_extension(filepath):
    """Detect programming language from file extension"""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby',
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql'
    }
    ext = Path(filepath).suffix.lower()
    return ext_map.get(ext, 'python')

def main():
    if len(sys.argv) < 3:
        print("Usage: python vscode_ai_helper.py <command> <server_ip> [file_path]")
        print("Commands: explain, review, test, generate")
        sys.exit(1)
    
    command = sys.argv[1]
    server_ip = sys.argv[2]
    
    # Get current file path if provided
    current_file = sys.argv[3] if len(sys.argv) > 3 else None
    language = detect_language_from_extension(current_file) if current_file else 'python'
    
    # Get selected text
    selected_text = get_selected_text()
    
    if not selected_text and command in ['explain', 'review', 'test']:
        print("Error: No text selected")
        sys.exit(1)
    
    # Get script directory (where ai.py should be)
    script_dir = Path(__file__).parent
    ai_script = script_dir / 'ai.py'
    
    if not ai_script.exists():
        print(f"Error: ai.py not found at {ai_script}")
        sys.exit(1)
    
    # For commands that need code input, write to temp file
    if selected_text and command in ['explain', 'review', 'test']:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(selected_text)
            temp_file = f.name
        
        try:
            # Build command
            cmd = [
                'python', str(ai_script),
                '--server', server_ip,
                command,
                '-l', language,
                '-f', temp_file
            ]
            
            # Run AI command
            subprocess.run(cmd)
        finally:
            # Clean up temp file
            os.unlink(temp_file)
    
    elif command == 'generate':
        # For generate, ask for description
        description = input("Describe the code to generate: ")
        cmd = [
            'python', str(ai_script),
            '--server', server_ip,
            'code',
            '-l', language,
            description
        ]
        subprocess.run(cmd)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()