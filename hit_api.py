import csv
import requests
import os 

url = "http://localhost:8000/api/process/"
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = '/Users/puramrahul/Documents/Hackathon/django_server/best_images_server/best_images_server/professional_cleaning_100_pros.csv'
k = 3  # Number of images you want per provider

# Group URLs by PROVIDERID
provider_urls = {}
print('Hii');

with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        provider_id = row['PROVIDERID'].strip()
        image_url = row['URL'].strip()

        if provider_id not in provider_urls:
            provider_urls[provider_id] = []
        provider_urls[provider_id].append(image_url)

print(f"Total Providers Found: {len(provider_urls)}")

# Send Request for each Provider
for provider_id, urls in provider_urls.items():
    print(f"\nProcessing PROVIDER: {provider_id}")

    payload = {
        "s3_urls": urls,
        "k": k
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print("Response:", response.json())

    except Exception as e:
        print(f"Error sending request for {provider_id}: {e}")
