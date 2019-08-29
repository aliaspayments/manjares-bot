import os
from pathlib import Path

import httpx
import slack
from bs4 import BeautifulSoup

IS_PRODUCTION = os.getenv("PYTHON_ENV") == "production"
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
MANJARES_URL = os.getenv("MANJARES_URL")

MENU_ITEM_IDENTIFIER = "🔹"
EXCLUDED_WORDS = ["hoy", "menú", "manjar"]


def get_website_data():

    # Use test file if not in production (avoid hitting FB in dev)
    if not IS_PRODUCTION:
        file = Path("test_data.html")
        with file.open() as fp:
            html = fp.read()
            return html

    headers = {"user-agent": "alias-payments-manjares-app/0.0.1"}

    response = httpx.get(MANJARES_URL, headers=headers)

    return response.text


def parse_html(website_html):
    soup = BeautifulSoup(website_html, "html5lib")
    recent_posts = soup.find(id="recent")

    results = []

    content = recent_posts.find("span").find_next("span")
    if not content:
        raise Exception("Content could not be extracted from latest post.")

    menu_list = content.find_all("p")
    if not menu_list:
        raise Exception("Could not obtain menu items from post.")

    facebook_link = content.find("a")["href"]
    return menu_list, facebook_link


def get_menu(menu_items):
    results = []

    for list_item in menu_items:
        data = list_item.get_text(strip=True)

        if MENU_ITEM_IDENTIFIER in data:
            menu_items = data.split(MENU_ITEM_IDENTIFIER)
            parsed_data = [" ".join(menu_item.split()) for menu_item in menu_items]
            results.extend(parsed_data)
        else:
            results.append(data)

    return results


def filter_menu(menu):
    filtered_menu = []

    normalized_items = [item.lower().strip() for item in menu]
    for item in normalized_items:
        if any([excluded_word in item for excluded_word in EXCLUDED_WORDS]):
            continue

        filtered_menu.append(item)

    return filtered_menu


def build_slack_message(menu_text):
    line_separated_items = "\n".join([f"- {text.lower()}" for text in menu_text])
    formatted_text = f"""                               _Menú de hoy en Manjares_ (<!here>):

{line_separated_items}
"""

    return formatted_text


def send_menu_to_slack(menu, facebook_link):
    client = slack.WebClient(token=SLACK_API_TOKEN)

    response = client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=menu,
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": menu}},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in Facebook"},
                        "url": f"https://mobile.facebook.com/{facebook_link}",
                    }
                ],
            },
        ],
        mrkdwn=True,
    )

    return response


def main(event, context):
    website_html = get_website_data()
    try:
        website_data, facebook_link = parse_html(website_html)
    except Exception as err:
        return {"message": f"Problem obtaining menu data: {err}"}

    raw_menu = get_menu(website_data)
    filtered_menu = filter_menu(raw_menu)
    slack_menu_message = build_slack_message(filtered_menu)

    try:
        response = send_menu_to_slack(slack_menu_message, facebook_link)
        return {"message": "Successfully posted message to Slack!"}
    except slack.errors.SlackApiError as err:
        return {"message": f"Problem posting message to Slack: {err}"}


if __name__ == "__main__":
    result = main(None, None)
    print(result["message"])
