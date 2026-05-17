import sqlite3
import json

conn = sqlite3.connect("caseforge.db")
cursor = conn.cursor()

print("\n" + "="*100)
print("CASEFORGE DATABASE REPORT")
print("="*100)

# CASES
print("\n📚 CASE STUDIES")
print("-"*100)
cursor.execute("SELECT id, title, industry, complexity, generation_time_ms, refinement_count, created_at FROM case_studies ORDER BY id")
cases = cursor.fetchall()
print(f"Total Cases: {len(cases)}\n")
for row in cases:
    print(f"ID: {row[0]:2d} | Title: {row[1][:40]:40s} | Industry: {row[2]:15s} | Level: {row[3]:15s} | Time: {row[4]:4d}ms | Refinements: {row[5]} | Date: {row[6]}")

# SOLUTIONS
print("\n\n✍️  SOLUTIONS & SCORES")
print("-"*100)
cursor.execute("SELECT id, user_id, case_id, overall_score, reasoning_score, communication_score, business_acumen_score, created_at FROM user_solutions ORDER BY id")
solutions = cursor.fetchall()
print(f"Total Solutions: {len(solutions)}\n")
if solutions:
    for row in solutions:
        print(f"ID: {row[0]} | User: {row[1]} | Case: {row[2]} | Overall: {row[3]}/10 | Reasoning: {row[4]}/10 | Comm: {row[5]}/10 | Acumen: {row[6]}/10 | Date: {row[7]}")

# SUMMARY STATS
print("\n\n📊 SUMMARY STATISTICS")
print("-"*100)
cursor.execute("SELECT COUNT(*) FROM case_studies")
total_cases = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_solutions")
total_solutions = cursor.fetchone()[0]

cursor.execute("SELECT industry, COUNT(*) FROM case_studies GROUP BY industry")
by_industry = cursor.fetchall()

cursor.execute("SELECT AVG(overall_score) FROM user_solutions")
avg_score = cursor.fetchone()[0]

cursor.execute("SELECT complexity, COUNT(*) FROM case_studies GROUP BY complexity")
by_complexity = cursor.fetchall()

print(f"Total Cases Generated: {total_cases}")
print(f"Total Solutions Submitted: {total_solutions}")
if avg_score:
    print(f"Average Solution Score: {avg_score:.2f}/10")
else:
    print(f"Average Solution Score: No solutions yet")

print(f"\nCases by Industry:")
for industry, count in by_industry:
    print(f"  - {industry}: {count}")

print(f"\nCases by Difficulty:")
for complexity, count in by_complexity:
    print(f"  - {complexity}: {count}")

print(f"\nAverage Generation Time: ", end="")
cursor.execute("SELECT AVG(generation_time_ms) FROM case_studies")
avg_gen_time = cursor.fetchone()[0]
print(f"{avg_gen_time:.0f}ms")

print("\n" + "="*100)
print("END OF REPORT")
print("="*100 + "\n")

conn.close()
