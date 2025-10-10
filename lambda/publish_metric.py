import boto3
import json
import time
import urllib.request


URLS = ['https://www.google.com','https://www.youtube.com','https://www.facebook.com']


cloudwatch = boto3.client('cloudwatch')


#check websites 
def check_website(url):
    start = time.time()
    try:
        response = urllib.request.urlopen(url, timeout=5)
        latency = (time.time() - start) * 1000  # ms
        availability = 1 if response.status == 200 else 0
    except Exception:
        latency = 0
        availability = 0
    return availability, latency


#push metrics 
def push_metrics(name, availability, latency):
    cloudwatch.put_metric_data(
        Namespace='Hungle',
        MetricData=[
            {
                'MetricName': 'Availability',
                'Dimensions': [{'Name': 'Website', 'Value': name}],
                'Value': availability,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Latency',  'Dimensions': [{'Name': 'Website', 'Value': name}],
                'Value': latency,
                'Unit': 'Milliseconds'
            }
        ]
    )

def handler(event, context):
    for url in URLS:
        availability, latency = check_website(url)
        print(f"{url} -> Availability: {availability}, Latency: {latency:.2f}ms")
        push_metrics(url, availability, latency)
    return {"status": "completed"}