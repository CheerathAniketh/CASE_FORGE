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

"""
solution template

curl -X POST http://localhost:8000/api/v1/solutions/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "case_id": 10,
    "solution": "TechCorp should shift from a reactive inbound-led sales model to a proactive enterprise sales strategy focused on large healthcare providers. The company'\''s biggest priorities should be enterprise relationship building, platform differentiation, scalable customization, and pricing flexibility. Large healthcare organizations typically involve long purchasing cycles, multiple stakeholders, compliance requirements, and complex integrations. Therefore, TechCorp must build a consultative sales process with dedicated enterprise account executives and solution engineers who understand healthcare workflows, security requirements, and integration challenges.\n\nThe company should prioritize investments in three stages. First, invest in enterprise sales infrastructure by hiring experienced enterprise sales representatives, customer success managers, and technical solution architects. This directly improves the ability to close large deals and manage long-term relationships. Second, develop strategic partnerships with healthcare IT vendors and EHR providers because integrations create switching costs and improve customer trust. Third, enhance platform capabilities selectively instead of trying to match every competitor feature. TechCorp should focus on features that directly improve ROI for healthcare providers, such as AI-driven patient engagement analytics, campaign optimization, and compliance automation.\n\nTechCorp should adopt a tiered pricing model instead of relying only on per-user pricing. Enterprise healthcare providers prefer predictable and flexible pricing structures. A tiered model could include basic, professional, and enterprise plans with optional add-ons for integrations, analytics, and premium support. The benefits include improved competitiveness against MedTech Inc., higher expansion revenue opportunities, and easier entry into large accounts. However, risks include pricing complexity, reduced short-term margins, and customer confusion if packages are poorly designed. To reduce these risks, TechCorp should keep pricing transparent and value-driven.\n\nData analytics and AI-driven insights should become central to the sales strategy. TechCorp already operates in AI-powered marketing automation, so it should leverage its own technology internally. Predictive analytics can identify high-value prospects, forecast churn, estimate upsell opportunities, and personalize enterprise demos. AI can also help sales teams understand customer pain points by analyzing usage data, engagement patterns, and healthcare marketing trends. This improves sales efficiency and shortens enterprise sales cycles.\n\nTo balance customization with scalability, TechCorp should create a modular platform architecture. Instead of building fully custom solutions for every client, the company should offer configurable modules and standardized APIs. This allows enterprise customers to integrate with existing systems while keeping development costs manageable. A standardized implementation framework and reusable integration templates will improve scalability and reduce onboarding time.\n\nThe company should monitor several KPIs to measure enterprise sales performance. Key metrics include enterprise deal conversion rate, annual recurring revenue (ARR), CAC payback period, customer retention rate, churn reduction, average contract value (ACV), sales cycle length, and net revenue retention (NRR). These metrics should be reviewed monthly at the operational level and quarterly at the strategic level.\n\nTechCorp should also challenge several hidden assumptions. Large healthcare providers may reduce spending if economic conditions tighten, so TechCorp must clearly demonstrate measurable ROI. Additionally, MedTech Inc.'s broader feature set may not necessarily translate into better customer outcomes. TechCorp can differentiate through ease of use, healthcare specialization, superior customer support, and faster deployment times. Finally, scaling sales does not only require more staff; improving sales efficiency through partnerships, automation, and customer success programs can produce stronger long-term results.\n\nOverall, TechCorp'\''s best strategy is to position itself as a specialized, AI-driven healthcare marketing partner rather than competing feature-for-feature with MedTech Inc. By combining enterprise-focused sales execution, strategic integrations, flexible pricing, and scalable customization, the company can realistically accelerate growth toward its $50 million revenue target while maintaining healthy margins and long-term customer relationships."
  }'
  
  """