import os
import json
import boto3
import urllib.parse

dynamodb = boto3.resource("dynamodb")
cw = boto3.client("cloudwatch")
table = dynamodb.Table(os.environ["TABLE_NAME"])
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
DASHBOARD_NAME = os.environ.get("DASHBOARD_NAME", "WebHealthDashboard")
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "Hungle")
AVAILABILITY_METRIC = os.environ.get("AVAILABILITY_METRIC", "Availability")
LATENCY_METRIC = os.environ.get("LATENCY_METRIC", "Latency")

def sanitize_for_name(s: str) -> str:
    # convert https://www.google.com -> https---www-google-com
    return s.replace("https://", "").replace("http://", "").replace(".", "-").replace("/", "-")

def make_alarm_name(prefix, url):
    return f"{prefix}-{sanitize_for_name(url)}"

def create_alarms_for_url(url):
    # Availability alarm: threshold 0 (meaning availability = 0 triggers)
    availability_alarm_name = make_alarm_name("AvailabilityAlarm", url)
    cw.put_metric_alarm(
        AlarmName=availability_alarm_name,
        AlarmDescription=f"Availability alarm for {url}",
        Namespace=METRIC_NAMESPACE,
        MetricName=AVAILABILITY_METRIC,
        Dimensions=[{"Name": "Website", "Value": url}],
        Statistic="Average",
        Period=300,
        EvaluationPeriods=1,
        ComparisonOperator="LessThanThreshold",
        Threshold=1,  # adjust depending on your metrics: here treat <1 as unavailable
        AlarmActions=[SNS_TOPIC_ARN] if SNS_TOPIC_ARN else []
    )

    # Latency alarm: threshold example 0.31 seconds
    latency_alarm_name = make_alarm_name("LatencyAlarm", url)
    cw.put_metric_alarm(
        AlarmName=latency_alarm_name,
        AlarmDescription=f"Latency alarm for {url}",
        Namespace=METRIC_NAMESPACE,
        MetricName=LATENCY_METRIC,
        Dimensions=[{"Name": "Website", "Value": url}],
        Statistic="Average",
        Period=300,
        EvaluationPeriods=1,
        ComparisonOperator="GreaterThanThreshold",
        Threshold=0.31,
        AlarmActions=[SNS_TOPIC_ARN] if SNS_TOPIC_ARN else []
    )

def delete_alarms_for_url(url):
    availability_alarm_name = make_alarm_name("AvailabilityAlarm", url)
    latency_alarm_name = make_alarm_name("LatencyAlarm", url)
    try:
        cw.delete_alarms(AlarmNames=[availability_alarm_name, latency_alarm_name])
    except Exception as e:
        print("delete_alarms error:", e)

def build_dashboard_widgets(urls):
    widgets = []
    x = 0
    y = 0
    width = 6
    height = 6
    for i, url in enumerate(urls):
        # Two-metric widget shows Availability and Latency
        widget = {
            "type": "metric",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "properties": {
                "metrics": [
                    [METRIC_NAMESPACE, AVAILABILITY_METRIC, "Website", url],
                    [METRIC_NAMESPACE, LATENCY_METRIC, "Website", url]
                ],
                "stat": "Average",
                "view": "timeSeries",
                "stacked": False,
                "region": os.environ.get("AWS_REGION", "us-east-1"),
                "title": f"Availability & Latency - {url}",
                "period": 60
            }
        }
        widgets.append(widget)
        x += width
        if x >= 24:
            x = 0
            y += height
    return widgets

def rebuild_dashboard_from_table():
    # scan table to gather current URLs
    resp = table.scan(ProjectionExpression="url")
    items = resp.get("Items", [])
    urls = [it["url"] for it in items if "url" in it]
    widgets = build_dashboard_widgets(urls)
    dashboard_body = {"widgets": widgets}
    try:
        cw.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=json.dumps(dashboard_body)
        )
    except Exception as e:
        print("put_dashboard error:", e)

def lambda_handler_record(record):
    eventName = record["eventName"]  # INSERT, MODIFY, REMOVE
    if eventName == "INSERT":
        newImage = record["dynamodb"].get("NewImage", {})
        url = newImage.get("url", {}).get("S")
        if url:
            create_alarms_for_url(url)
            # after creating alarms, rebuild dashboard
            rebuild_dashboard_from_table()
    elif eventName == "MODIFY":
        # On modify, best to rebuild alarms & dashboard in case URL changed
        newImage = record["dynamodb"].get("NewImage", {})
        oldImage = record["dynamodb"].get("OldImage", {})
        new_url = newImage.get("url", {}).get("S")
        old_url = oldImage.get("url", {}).get("S")
        if new_url and old_url and new_url != old_url:
            # delete old alarms, create new ones, rebuild dashboard
            delete_alarms_for_url(old_url)
            create_alarms_for_url(new_url)
            rebuild_dashboard_from_table()
    elif eventName == "REMOVE":
        oldImage = record["dynamodb"].get("OldImage", {})
        url = oldImage.get("url", {}).get("S")
        if url:
            delete_alarms_for_url(url)
            rebuild_dashboard_from_table()

def handler(event, context):
    # event contains Records from DynamoDB Stream
    records = event.get("Records", [])
    for rec in records:
        try:
            lambda_handler_record(rec)
        except Exception as e:
            print("Error handling record:", e, rec)
    return {"statusCode": 200, "body": json.dumps({"message": "Processed stream records", "count": len(records)})}
