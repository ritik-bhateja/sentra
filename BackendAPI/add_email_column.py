import csv

# Read the CSV file
input_file = 'INSURANCE_DATA.csv'
output_file = 'INSURANCE_DATA.csv'

# Read all rows
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

# Add 'email' to fieldnames if not already present
if 'email' not in fieldnames:
    fieldnames = list(fieldnames) + ['email']

# Email distribution
# 10 to harsh.kumar@sentra.com
# 20 to vishal.saxena@sentra.com  
# 30 to kamaljeet.singh@sentra.com
# 40 to super.admin@sentra.com
# Total = 100 rows

email_assignments = []
email_assignments.extend(['harsh.kumar@sentra.com'] * 10)
email_assignments.extend(['vishal.saxena@sentra.com'] * 20)
email_assignments.extend(['kamaljeet.singh@sentra.com'] * 30)
email_assignments.extend(['super.admin@sentra.com'] * 40)

# Assign emails to rows
for i, row in enumerate(rows):
    if i < len(email_assignments):
        row['email'] = email_assignments[i]
    else:
        # If there are more rows than 100, cycle through the pattern
        row['email'] = email_assignments[i % len(email_assignments)]

# Write back to CSV
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Successfully added email column to {len(rows)} rows")
print(f"Distribution:")
print(f"  harsh.kumar@sentra.com: {sum(1 for r in rows if r.get('email') == 'harsh.kumar@sentra.com')}")
print(f"  vishal.saxena@sentra.com: {sum(1 for r in rows if r.get('email') == 'vishal.saxena@sentra.com')}")
print(f"  kamaljeet.singh@sentra.com: {sum(1 for r in rows if r.get('email') == 'kamaljeet.singh@sentra.com')}")
print(f"  super.admin@sentra.com: {sum(1 for r in rows if r.get('email') == 'super.admin@sentra.com')}")
