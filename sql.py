import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
import os

# Create the SQLite database engine
engine = create_engine("sqlite:///database.sqlite")

# Directory containing your CSV files
csv_directory = "data"

# List of your CSV files in the directory
csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]

for filename in csv_files:
    # Construct the full file path
    file_path = os.path.join(csv_directory, filename)
    
    # Load the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Display the first 5 rows
    print(f"First 5 rows of {filename}:")
    print(df.head())
    
    # Extract the table name from the filename
    table_name = filename.split(".")[0]
    
    # Append the data to the SQLite database
    df.to_sql(table_name, engine, if_exists="append", index=False)

# Create a metadata object and reflect the database schema
metadata = MetaData()
metadata.reflect(bind=engine)

for filename in csv_files:
    # Extract the table name from the filename
    table_name = filename.split(".")[0]
    
    # Define the table
    qualifying_table = Table(table_name, metadata, autoload_with=engine)

    # Perform a select query to verify the data
    query = qualifying_table.select().limit(10)

    # Execute the query and print the results
    print(f"First 10 rows of the table {table_name}:")
    with engine.connect() as connection:
        result = connection.execute(query)
        for row in result:
            print(row)