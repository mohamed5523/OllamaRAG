#!/usr/bin/env python3
"""
R&D AI CLI - Advanced terminal-based AI assistant
Usage: python ai.py [command] [options]

Network Usage:
  python ai.py --server 192.168.1.100 "your question"
  python ai.py -s YOUR_IP interactive
"""

import requests
import json
import sys
import os
from typing import Optional, List, Dict
import argparse

class R_D_AI:
    def __init__(self, server_host: str = "localhost", ollama_port: str = "11434", rag_port: str = "8001"):
        self.ollama_host = f"http://{server_host}:{ollama_port}"
        self.rag_api_host = f"http://{server_host}:{rag_port}"
        self.model = "qwen2.5-coder:7b-instruct-q5_K_M"
        self.server_host = server_host
        
    def chat(self, prompt: str, use_rag: bool = False, stream: bool = True):
        """Send a chat message to the AI"""
        
        # If RAG is enabled, get context first
        if use_rag:
            context = self._get_rag_context(prompt)
            if context:
                prompt = f"Context from R&D documents:\n{context}\n\nQuestion: {prompt}"
        
        url = f"{self.ollama_host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": stream}
        
        try:
            response = requests.post(url, json=payload, stream=stream, timeout=120)
            response.raise_for_status()
            
            if stream:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get('response', '')
                        full_response += token
                        print(token, end='', flush=True)
                print()
                return full_response
            else:
                return response.json().get('response', '')
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Cannot connect to AI server at {self.ollama_host}", file=sys.stderr)
            print(f"   Make sure the server is running and accessible from this device.", file=sys.stderr)
            return ""
        except requests.exceptions.Timeout:
            print(f"\n❌ Request timed out. The AI server may be busy.", file=sys.stderr)
            return ""
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            return ""
    
    def _get_rag_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context from R&D documents"""
        try:
            response = requests.post(
                f"{self.rag_api_host}/search",
                json={"query": query, "top_k": top_k},
                timeout=5
            )
            if response.status_code == 200:
                results = response.json()
                contexts = [r.get('text', '') for r in results]
                return "\n\n".join(contexts[:top_k])
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Cannot reach RAG API at {self.rag_api_host}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  RAG search failed: {e}", file=sys.stderr)
        return ""
    
    def explain_code(self, code: str, language: str = "python"):
        """Explain a code snippet"""
        prompt = f"Explain this {language} code in detail:\n\n```{language}\n{code}\n```"
        return self.chat(prompt)
    
    def review_code(self, code: str, language: str = "python"):
        """Review code for issues"""
        prompt = f"""Review this {language} code for:
1. Bugs and potential errors
2. Performance issues
3. Security vulnerabilities
4. Best practices violations
5. Suggestions for improvement

Code:
```{language}
{code}
```"""
        return self.chat(prompt)
    
    def generate_code(self, description: str, language: str = "python"):
        """Generate code from description"""
        prompt = f"Write clean, production-ready {language} code that does:\n\n{description}\n\nProvide only the code with minimal comments."
        return self.chat(prompt)
    
    def generate_tests(self, code: str, language: str = "python"):
        """Generate unit tests"""
        prompt = f"Generate comprehensive unit tests for this {language} code:\n\n```{language}\n{code}\n```"
        return self.chat(prompt)
    
    def debug_code(self, code: str, error: str, language: str = "python"):
        """Help debug code"""
        prompt = f"""Debug this {language} code:

Code:
```{language}
{code}
```

Error: {error}

Explain the issue and provide a fix."""
        return self.chat(prompt)
    
    def search_docs(self, query: str, top_k: int = 3):
        """Search R&D documents"""
        try:
            response = requests.post(
                f"{self.rag_api_host}/search",
                json={"query": query, "top_k": top_k},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"⚠️  Search failed: {e}", file=sys.stderr)
            return []
    
    def switch_model(self, model_name: str):
        """Switch to a different model"""
        models = {
            "deepseek": "deepseek-coder-v2:16b-lite-instruct-q4_K_M",
            "qwen": "qwen2.5-coder:7b-instruct-q5_K_M",
            "fast": "qwen2.5-coder:7b-instruct-q5_K_M"
        }
        if model_name in models:
            self.model = models[model_name]
            print(f"✓ Switched to {model_name}: {self.model}")
        else:
            self.model = model_name
            print(f"✓ Switched to: {model_name}")
    
    def test_connection(self):
        """Test connection to AI server"""
        print(f"🔍 Testing connection to {self.ollama_host}...")
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"✅ Connected! Available models: {len(models)}")
                return True
            else:
                print(f"⚠️  Server responded with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {self.ollama_host}")
            print(f"   Make sure:")
            print(f"   1. The AI server is running")
            print(f"   2. You're on the same network")
            print(f"   3. The server IP is correct: {self.server_host}")
            print(f"   4. Firewall allows connections on port 11434")
            return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description='R&D AI CLI - Network-enabled AI Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Local usage:
    python ai.py "explain async/await"
    python ai.py interactive
    
  Remote usage:
    python ai.py --server 192.168.1.100 "write a hello world"
    python ai.py -s 192.168.1.100 interactive
    python ai.py --server 10.0.0.5 code "fibonacci function"
    
  With RAG:
    python ai.py -s 192.168.1.100 -r "what are our coding standards?"
        """
    )
    
    parser.add_argument('command', nargs='?', default='interactive',
                       choices=['chat', 'code', 'explain', 'review', 'test', 'search', 'interactive'],
                       help='Command to execute')
    parser.add_argument('prompt', nargs='*', help='Prompt text')
    parser.add_argument('-s', '--server', type=str, default='localhost',
                       help='AI server IP address (default: localhost)')
    parser.add_argument('--port', type=str, default='11434',
                       help='Ollama server port (default: 11434)')
    parser.add_argument('--rag-port', type=str, default='8001',
                       help='RAG API port (default: 8001)')
    parser.add_argument('-f', '--file', type=str, help='File containing code')
    parser.add_argument('-l', '--language', type=str, default='python', help='Programming language')
    parser.add_argument('-r', '--rag', action='store_true', help='Enable RAG')
    parser.add_argument('--fast', action='store_true', help='Use fast model')
    parser.add_argument('--test', action='store_true', help='Test connection to server')
    
    args = parser.parse_args()
    
    # Initialize AI with server settings
    ai = R_D_AI(
        server_host=args.server,
        ollama_port=args.port,
        rag_port=args.rag_port
    )
    
    # Show connection info if not localhost
    if args.server != 'localhost':
        print(f"🌐 Connecting to AI server: {args.server}")
    
    # Test connection if requested
    if args.test:
        ai.test_connection()
        return
    
    # Switch to fast model if requested
    if args.fast:
        ai.switch_model("fast")
    
    # Get input
    input_text = ""
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
    elif args.prompt:
        input_text = " ".join(args.prompt)
    
    # Execute command
    if args.command == 'chat':
        if not input_text:
            print("❌ Provide prompt")
            return
        print(f"\n💬 Using: {ai.model.split(':')[0]}\n")
        ai.chat(input_text, use_rag=args.rag)
    
    elif args.command == 'code':
        if not input_text:
            print("❌ Provide description")
            return
        print(f"\n💬 Using: {ai.model.split(':')[0]}\n")
        ai.generate_code(input_text, args.language)
    
    elif args.command == 'explain':
        if not input_text:
            print("❌ Provide code with -f")
            return
        print(f"\n💬 Using: {ai.model.split(':')[0]}\n")
        ai.explain_code(input_text, args.language)
    
    elif args.command == 'review':
        if not input_text:
            print("❌ Provide code with -f")
            return
        print(f"\n💬 Using: {ai.model.split(':')[0]}\n")
        ai.review_code(input_text, args.language)
    
    elif args.command == 'test':
        if not input_text:
            print("❌ Provide code with -f")
            return
        print(f"\n💬 Using: {ai.model.split(':')[0]}\n")
        ai.generate_tests(input_text, args.language)
    
    elif args.command == 'search':
        if not input_text:
            print("❌ Provide query")
            return
        results = ai.search_docs(input_text)
        if results:
            print(f"\n📚 Found {len(results)} results:\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. {r.get('metadata', {}).get('filename', 'Unknown')}")
                print(f"   {r.get('text', '')[:150]}...\n")
        else:
            print("No results found")
    
    elif args.command == 'interactive':
        print("╔════════════════════════════════════════╗")
        print("║     R&D AI - Interactive Mode          ║")
        print("╚════════════════════════════════════════╝")
        print(f"\nServer: {ai.ollama_host}")
        print(f"Model: {ai.model}")
        print("\nCommands:")
        print("  /rag on|off    - Toggle RAG")
        print("  /model <name>  - Switch model (deepseek, qwen, fast)")
        print("  /search <q>    - Search documents")
        print("  /test          - Test connection")
        print("  exit/quit      - Exit\n")
        
        use_rag = args.rag
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.startswith('/'):
                    cmd_parts = user_input[1:].split(maxsplit=1)
                    cmd = cmd_parts[0].lower()
                    
                    if cmd == 'rag':
                        if len(cmd_parts) > 1 and cmd_parts[1].lower() == 'on':
                            use_rag = True
                            print("✓ RAG enabled")
                        else:
                            use_rag = False
                            print("✓ RAG disabled")
                        continue
                    
                    elif cmd == 'model':
                        if len(cmd_parts) > 1:
                            ai.switch_model(cmd_parts[1])
                        continue
                    
                    elif cmd == 'search':
                        if len(cmd_parts) > 1:
                            results = ai.search_docs(cmd_parts[1])
                            if results:
                                for i, r in enumerate(results, 1):
                                    print(f"{i}. {r.get('metadata', {}).get('filename')}")
                                    print(f"   {r.get('text', '')[:100]}...\n")
                        continue
                    
                    elif cmd == 'test':
                        ai.test_connection()
                        continue
                
                print("\nAI: ", end='', flush=True)
                ai.chat(user_input, use_rag=use_rag)
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                break

if __name__ == '__main__':
    main()