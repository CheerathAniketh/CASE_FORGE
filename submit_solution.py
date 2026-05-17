import requests
import sys

API_URL = "http://localhost:8000/api/v1/solutions/evaluate"

def submit_solution(user_id, case_id, solution_text):
    """Submit a solution to a case"""
    payload = {
        "user_id": user_id,
        "case_id": case_id,
        "solution": solution_text
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "="*100)
            print("✅ SOLUTION SUBMITTED SUCCESSFULLY")
            print("="*100)
            print(f"\nSolution ID: {data['solution_id']}")
            print(f"\n📊 SCORES:")
            print(f"  Overall: {data['scores']['overall']}/10")
            print(f"  Problem Understanding: {data['scores']['problem_understanding']}/10")
            print(f"  Analytical Rigor: {data['scores']['analytical_rigor']}/10")
            print(f"  Business Acumen: {data['scores']['business_acumen']}/10")
            print(f"  Communication: {data['scores']['communication']}/10")
            
            feedback = data['feedback']
            print(f"\n✅ STRENGTHS:")
            for s in feedback.get('strengths', []):
                print(f"  - {s}")
            
            print(f"\n⚠️  WEAKNESSES:")
            for w in feedback.get('weaknesses', []):
                print(f"  - {w}")
            
            print(f"\n💡 SUGGESTIONS:")
            for sug in feedback.get('suggestions', []):
                print(f"  - {sug}")
            
            print(f"\n📋 FEEDBACK:")
            print(f"  {feedback.get('feedback', 'N/A')}")
            print("\n" + "="*100 + "\n")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*100)
    print("SUBMIT SOLUTION")
    print("="*100)
    
    user_id = int(input("\nEnter User ID: "))
    case_id = int(input("Enter Case ID: "))
    
    print("\nPaste your solution (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
        lines.append(line)
    
    solution_text = "\n".join(lines[:-1])  # Remove last empty line
    
    submit_solution(user_id, case_id, solution_text)
