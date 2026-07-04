import csv
from faker import Faker

fake = Faker()
domain = "tonytaylor567hotmail.onmicrosoft.com"  # Your actual domain

with open('employees.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['firstName', 'lastName', 'department', 'role', 'email'])
    
    departments = ['Finance', 'Engineering', 'Sales', 'HR']
    roles = {
        'Finance': ['Analyst', 'Controller', 'Manager'],
        'Engineering': ['Developer', 'Lead', 'Architect'],
        'Sales': ['Representative', 'Manager', 'Director'],
        'HR': ['Specialist', 'Manager', 'Coordinator']
    }
    
    for _ in range(100):
        first_name = fake.first_name()
        last_name = fake.last_name()
        department = fake.random_element(departments)
        role = fake.random_element(roles[department])
        email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        writer.writerow([first_name, last_name, department, role, email])

print("✅ Generated 100 users in employees.csv")