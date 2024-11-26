# app.py
from aws_cdk import App, Environment
from jpholiday.jpholiday_stack import JpHolidayStack
from dotenv import load_dotenv
import os

load_dotenv()

app = App()
JpHolidayStack(app, f"JpHolidayStack-{os.getenv('STAGE')}",
    env=Environment(
        account=os.getenv('AWS_ACCOUNT'),
        region=os.getenv('AWS_REGION')
    )
)
app.synth()
