import sqlite3
import json

conn = sqlite3.connect("caseforge.db")
cursor = conn.cursor()

print("\n" + "="*120)
print("DETAILED CASE STUDIES VIEW")
print("="*120)

cursor.execute("SELECT id, title, industry, complexity, case_data FROM case_studies ORDER BY id")
cases = cursor.fetchall()

for case in cases:
    case_id, title, industry, complexity, case_data_json = case
    case_data = json.loads(case_data_json)
    
    print(f"\n{'='*120}")
    print(f"CASE #{case_id}: {title}")
    print(f"{'='*120}")
    print(f"Industry: {industry} | Difficulty: {complexity}")
    
    print(f"\n📍 COMPANY: {case_data.get('company_name', 'N/A')}")
    print(f"Background: {case_data.get('company_background', 'N/A')[:200]}...")
    
    print(f"\n📋 SCENARIO OVERVIEW:")
    print(case_data.get('scenario_overview', 'N/A')[:300])
    
    print(f"\n💰 KEY METRICS:")
    metrics = case_data.get('key_metrics', {})
    for metric, value in metrics.items():
        print(f"  - {metric}: {value}")
    
    print(f"\n❓ DISCUSSION QUESTIONS:")
    questions = case_data.get('discussion_questions', [])
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    
    print(f"\n  HIDDEN ASSUMPTIONS:")
    assumptions = case_data.get('hidden_assumptions', [])
    for assumption in assumptions:
        print(f"  - {assumption}")
    
    print(f"\n✅SOLUTION FRAMEWORK:")
    print(f"  {case_data.get('solution_framework', 'N/A')}")

print(f"\n\n{'='*120}")
print("END OF DETAILED REPORT")
print("="*120 + "\n")

conn.close()
