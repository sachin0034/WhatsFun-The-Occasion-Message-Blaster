from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB connection
mongo_client = MongoClient('')
db = mongo_client['guest_database']
collection = db['guests']

# Drop existing collection (if any)
collection.drop()

# Get current date
current_date = datetime.now()

# Sample data
sample_data = [
    {
        "name": "Sachin",
        "check_in_date": (current_date - timedelta(days=1)).strftime("%Y-%m-%d"),
        "birthday_date": current_date.strftime("%Y-%m-%d"),
        "anniversary_date": (current_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "mobile_number": ""
    },
    {
        "name": "John Doe",
        "check_in_date": current_date.strftime("%Y-%m-%d"),
        "birthday_date": (current_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "anniversary_date": (current_date + timedelta(days=16)).strftime("%Y-%m-%d"),
        "mobile_number": ""
    },
    {
        "name": "Jane Smith",
        "check_in_date": (current_date - timedelta(days=2)).strftime("%Y-%m-%d"),
        "birthday_date": (current_date + timedelta(days=6)).strftime("%Y-%m-%d"),
        "anniversary_date": current_date.strftime("%Y-%m-%d"),
        "mobile_number": ""
    },
    {
        "name": "Alex Johnson",
        "check_in_date": (current_date - timedelta(days=3)).strftime("%Y-%m-%d"),
        "birthday_date": current_date.strftime("%Y-%m-%d"),
        "anniversary_date": (current_date + timedelta(days=33)).strftime("%Y-%m-%d"),
        "mobile_number": ""
    }
]

# Insert data into the collection
result = collection.insert_many(sample_data)

print(f"Inserted {len(result.inserted_ids)} documents into the database.")

# Verify the inserted data
for doc in collection.find():
    print(doc)

# Close the MongoDB connection
mongo_client.close()