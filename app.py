"""AWS CDK application entry point for Japanese Holiday Calendar."""
import os

from aws_cdk import App, Environment
from dotenv import load_dotenv

from jpholiday.jpholiday_stack import JpHolidayStack

load_dotenv()

app = App()
JpHolidayStack(
    app,
    f"JpHolidayStack-{os.getenv('STAGE')}",
    env=Environment(account=os.getenv("AWS_ACCOUNT"), region=os.getenv("AWS_REGION")),
)
app.synth()
