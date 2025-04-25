from supabase import create_client
import os

# Replace these with your actual Supabase URL and key
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

# Initialize the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Example: Create a table in Supabase
def create_table_example():
    # Note: Creating tables is typically done through the Supabase dashboard
    # or using database migrations, not directly in application code
    print("Tables are typically created through the Supabase dashboard")
    print("Go to: https://app.supabase.com > Your Project > Table Editor > New Table")

# Example: Insert data into a table
def insert_data_example():
    try:
        # Insert a new record into a table called 'tools'
        # (You need to create this table first in the Supabase dashboard)
        data = {
            "name": "Image Compression",
            "category": "Image Tools",
            "description": "Compress images without losing quality",
            "is_completed": True
        }
        
        response = supabase.table('tools').insert(data).execute()
        print("Data inserted successfully:")
        print(response.data)
        return response.data
    except Exception as e:
        print(f"Error inserting data: {e}")
        return None

# Example: Query data from a table
def query_data_example():
    try:
        # Query all tools that are completed
        response = supabase.table('tools').select('*').eq('is_completed', True).execute()
        print("Query results:")
        print(response.data)
        return response.data
    except Exception as e:
        print(f"Error querying data: {e}")
        return None

# Example: Update data in a table
def update_data_example(id):
    try:
        # Update a record
        data = {"description": "Updated description"}
        response = supabase.table('tools').update(data).eq('id', id).execute()
        print("Data updated successfully:")
        print(response.data)
        return response.data
    except Exception as e:
        print(f"Error updating data: {e}")
        return None

# Example: Delete data from a table
def delete_data_example(id):
    try:
        # Delete a record
        response = supabase.table('tools').delete().eq('id', id).execute()
        print("Data deleted successfully:")
        print(response.data)
        return response.data
    except Exception as e:
        print(f"Error deleting data: {e}")
        return None

# Run examples
if __name__ == "__main__":
    print("Supabase Python Client Example")
    print("------------------------------")
    print("Before running this example, make sure to:")
    print("1. Create a Supabase account and project")
    print("2. Replace SUPABASE_URL and SUPABASE_KEY with your actual values")
    print("3. Create a 'tools' table in your Supabase project with columns:")
    print("   - id (int8, primary key)")
    print("   - name (text)")
    print("   - category (text)")
    print("   - description (text)")
    print("   - is_completed (boolean)")
    print("\nTo create the table, go to the Supabase dashboard > Table Editor > New Table")
    
    # Uncomment these lines to run the examples
    # create_table_example()
    # new_record = insert_data_example()
    # if new_record:
    #     record_id = new_record[0]['id']
    #     query_data_example()
    #     update_data_example(record_id)
    #     delete_data_example(record_id)
