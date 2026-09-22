"""
Entry point for running TaskFlow application.
Execute with: python run.py
"""
import os
from backend import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1').lower() in ('true', '1')
    print("=" * 60)
    print("  TaskFlow - Organize your work. Clear your mind.")
    print(f"  Server starting at: http://127.0.0.1:{port}")
    print(f"  Debug mode: {debug}")
    print("=" * 60)
    app.run(host='127.0.0.1', port=port, debug=debug)
