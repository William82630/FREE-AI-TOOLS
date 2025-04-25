# Integrating Supabase with FREE AI TOOLS

This guide explains how to integrate Supabase with your existing FREE AI TOOLS Flask application.

## Step 1: Add Supabase Client to app.py

Add the following code near the top of your app.py file:

```python
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

# Initialize the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```

## Step 2: Create Database Tables

In your Supabase dashboard, create the necessary tables for your application. For example:

### Tools Table
- id (int8, primary key)
- name (text)
- category (text)
- description (text)
- is_completed (boolean)

### User Uploads Table (Optional)
- id (int8, primary key)
- user_id (text, if you implement authentication)
- file_name (text)
- file_path (text)
- created_at (timestamp with time zone)

## Step 3: Replace File Storage with Supabase Storage

Instead of storing files locally, you can use Supabase Storage:

```python
@app.route('/tools/image-editing/compress-image', methods=['GET', 'POST'])
def compress_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        try:
            # Read the file content
            content = file.read()
            
            # Upload to Supabase Storage
            file_path = f"compressed/{file.filename}"
            supabase.storage.from_('uploads').upload(file_path, content)
            
            # Get public URL
            file_url = supabase.storage.from_('uploads').get_public_url(file_path)
            
            # Process the image as before...
            
            # Return the Supabase URL instead of local path
            return jsonify({
                'success': True,
                'file_url': file_url,
                # Other response data...
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('compress_image.html')
```

## Step 4: Replace Local Data with Supabase Database

For tools that need to store data, use Supabase tables instead of local variables:

```python
@app.route('/api/tools', methods=['GET'])
def get_tools():
    try:
        # Query all tools from the database
        response = supabase.table('tools').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Step 5: Add Authentication (Optional)

If you want to add user authentication:

```python
@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        email = request.json.get('email')
        password = request.json.get('password')
        
        # Sign up user with Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        email = request.json.get('email')
        password = request.json.get('password')
        
        # Sign in user with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Benefits of Using Supabase

1. **Simplified Backend**: Reduce the amount of backend code you need to write
2. **Database & Storage**: Store both data and files in one platform
3. **Authentication**: Add user accounts and authentication easily
4. **Real-time Updates**: Subscribe to database changes for real-time features
5. **Scalability**: Supabase handles scaling as your application grows

## Next Steps

1. Create all necessary tables in Supabase
2. Update your API endpoints to use Supabase
3. Migrate your file storage to Supabase Storage
4. Add authentication if needed
5. Test thoroughly before deploying
