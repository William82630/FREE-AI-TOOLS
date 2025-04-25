from flask import Flask, render_template, request, jsonify
from supabase import create_client
import os

app = Flask(__name__)

# Replace these with your actual Supabase URL and key
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

# Initialize the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('supabase_example.html')

@app.route('/api/tools', methods=['GET'])
def get_tools():
    try:
        # Query all tools from the database
        response = supabase.table('tools').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools', methods=['POST'])
def add_tool():
    try:
        # Get data from request
        data = request.json
        
        # Insert data into the database
        response = supabase.table('tools').insert(data).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/<int:id>', methods=['PUT'])
def update_tool(id):
    try:
        # Get data from request
        data = request.json
        
        # Update data in the database
        response = supabase.table('tools').update(data).eq('id', id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/<int:id>', methods=['DELETE'])
def delete_tool(id):
    try:
        # Delete data from the database
        response = supabase.table('tools').delete().eq('id', id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
