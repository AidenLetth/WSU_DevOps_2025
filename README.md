
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

Web Crawler Monitoring Project – 
1. Project Purpose

This project builds a website monitoring system using AWS CDK, Lambda, CloudWatch, and DynamoDB, with a CRUD API to manage the list of websites to crawl.

Main goals:

Measure website availability and latency.

Store and monitor metrics in CloudWatch.

Trigger alerts when websites are down or slow.

Provide an API for adding, updating, deleting, and reading websites.

Deploy using a multi-stage pipeline with Beta/Gamma/Prod environments.

2. Completed Tasks
Web Crawler & Canary

Created a Lambda function running every 5 minutes.

Lambda performs:

Measuring availability and latency for each website.

Writing metrics to CloudWatch for each run.

Logging alerts to DynamoDB if a website is unavailable or slow.

Function acts as a canary for early detection of website issues.

CRUD API

Implemented API Gateway for CRUD operations on the website list.

Integrated with DynamoDB for persistent storage.

Fully implemented endpoints:

GET /targets → List all websites.

POST /targets → Add a new website.

PUT /targets/{id} → Update an existing website.

DELETE /targets/{id} → Remove a website.

Metrics & Dashboard

Created CloudWatch dashboard to monitor websites and the Lambda crawler.

Metrics tracked:

Availability, latency, memory usage, runtime.

Configured alarms for metric thresholds.

Alerts are sent via SNS/SQS with tags to classify metric type.

Multi-Stage Pipeline

Set up CDK pipeline with stages: Beta → Gamma → Prod.

Each stage includes test blockers to ensure all unit/integration tests pass.

Supports automatic rollback if metrics indicate failure.

Testing

Wrote unit tests for crawler logic and API CRUD operations.

Wrote integration tests:

Validate Lambda crawling and CloudWatch metrics.

Check DynamoDB read/write operations.

Test API Gateway CRUD functionality.

Monitored crawler performance: memory usage and processing time per run.

3. Technologies Used

AWS Lambda – periodic web crawler.

AWS CloudWatch – metrics, dashboard, alarms.

AWS DynamoDB – website list storage and alert logging.

AWS SNS / SQS – alerts and notification distribution.

AWS API Gateway – CRUD API endpoints.

AWS CDK – infrastructure and pipeline deployment.

Python 3.13 – Lambda code and tests.

pytest – unit and integration testing.
