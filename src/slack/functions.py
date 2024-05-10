from datetime import datetime, timedelta
import requests
import json
import boto3
import pandas as pd

import dotenv
dotenv.load_dotenv(override=True)


def send_message(token: str, channel_id: str, text: str) -> requests.Response:
    """This function is used send to message to Slack.

    Args:
        token (str): Slack bot token.
        channel_id (str): Slack channel id.
        text (str): Message to be send.

    Returns:
        requests.Response:
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    data = json.dumps({
        "channel": channel_id,
        "text": text
    })

    response = requests.post(
        url='https://slack.com/api/chat.postMessage',
        data=data,
        headers=headers
    )

    return response


def aws_cost_report(token: str, channel_id: str, fault_contact: str):
    client = boto3.client('ce')

    current_date = datetime.now()
    start_date = current_date - timedelta(days=2)
    end_date = current_date - timedelta(days=1)

    date_format = "%Y-%m-%d"
    today_text = end_date.strftime(date_format)
    yesterday_text = start_date.strftime(date_format)

    response: dict = client.get_cost_and_usage(
        TimePeriod={
            'Start': yesterday_text,
            'End': today_text
        },
        Granularity='DAILY',
        Metrics=["UnblendedCost"],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            },
        ],
    )

    if 'NextPageToken' in response.keys():
        send_message(token, channel_id,
                     f"<@{fault_contact} aws_cost_report response contain NextPageToken!>")
        # TODO should add logging
        exit(1)

    try:
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            send_message(
                token, channel_id, f"<@{fault_contact} aws_cost_report response is not 200!>")
    except:
        send_message(token, channel_id,
                     f"<@{fault_contact} aws_cost_report could not get response properly!>")

    results = response['ResultsByTime'][0]

    total_cost = 0
    for group in results['Groups']:
        total_cost += float(group['Metrics']['UnblendedCost']['Amount'])

    message = f"*AWS Daily Cost Report*\n"
    message += f"{results['TimePeriod']['Start']} \
        Total cost: {total_cost:.2f} USD\n"

    data = [(item["Keys"][0],
             float(item["Metrics"]["UnblendedCost"]["Amount"]),
             item["Metrics"]["UnblendedCost"]["Unit"]) for item in results['Groups']]

    df = pd.DataFrame(data)
    df.columns = ["Service", "Amount", "Unit"]
    df.sort_values("Amount", inplace=True, ascending=False)
    df['Amount'] = df['Amount'].apply("{:.2f}".format)

    message += f"```{df.to_string(index=False)}```\n"

    message += f"_This report generated from AWS Cost Explorer's estimated data._"

    send_message(token, channel_id, message)
