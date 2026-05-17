import sqlite3
import json

conn = sqlite3.connect("caseforge.db")
cursor = conn.cursor()

print("\n" + "="*120)
print("CASE STUDIES - FULL JSON DATA")
print("="*120)

cursor.execute("SELECT id, title, case_data FROM case_studies ORDER BY id")
cases = cursor.fetchall()

for case_id, title, case_data_json in cases:
    case_data = json.loads(case_data_json)
    
    print(f"\n\n{'='*120}")
    print(f"CASE #{case_id}: {title}")
    print(f"{'='*120}\n")
    
    # Pretty print the JSON
    print(json.dumps(case_data, indent=2))

print(f"\n\n{'='*120}")
print("END OF JSON DATA")
print("="*120 + "\n")

conn.close()
