import sqlite3
import json

conn = sqlite3.connect("caseforge.db")
cursor = conn.cursor()

print("\n" + "="*120)
print("SUBMITTED SOLUTIONS - FULL DETAILS")
print("="*120)

cursor.execute("SELECT id, user_id, case_id, solution_text, overall_score, reasoning_score, communication_score, business_acumen_score, feedback_data FROM user_solutions ORDER BY id")
solutions = cursor.fetchall()

if not solutions:
    print("\n❌ No solutions submitted yet!")
else:
    for sol in solutions:
        sol_id, user_id, case_id, solution_text, overall, reasoning, comm, acumen, feedback_json = sol
        feedback = json.loads(feedback_json) if feedback_json else {}
        
        print(f"\n\n{'='*120}")
        print(f"SOLUTION #{sol_id} | User {user_id} → Case #{case_id}")
        print(f"{'='*120}")
        
        print(f"\n📝 SOLUTION TEXT:")
        print(f"{solution_text[:500]}...")
        
        print(f"\n📊 SCORES:")
        print(f"  Overall: {overall}/10")
        print(f"  Reasoning: {reasoning}/10")
        print(f"  Communication: {comm}/10")
        print(f"  Business Acumen: {acumen}/10")
        
        print(f"\n✅ STRENGTHS:")
        for strength in feedback.get('strengths', []):
            print(f"  - {strength}")
        
        print(f"\n⚠️  WEAKNESSES:")
        for weakness in feedback.get('weaknesses', []):
            print(f"  - {weakness}")
        
        print(f"\n💡 SUGGESTIONS:")
        for suggestion in feedback.get('suggestions', []):
            print(f"  - {suggestion}")
        
        print(f"\n📋 FEEDBACK:")
        print(f"  {feedback.get('feedback', 'N/A')}")

print(f"\n\n{'='*120}")
print("END OF SOLUTIONS REPORT")
print("="*120 + "\n")

conn.close()


