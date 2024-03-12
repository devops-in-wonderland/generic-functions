import requests
import json

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

