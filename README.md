# Manjares Slack Bot

## Description

This is a Slack bot which posts the menu for [Manjares Café & Grill](https://www.facebook.com/ManjaresCafeGrill) daily on the channel of your choice.

It works by scraping the mobile Facebook page for the café, where the café staff post the menu daily in a consistent manner (so far).

## Installation

You can use the [Serverless framework](https://github.com/serverless/serverless) to deploy on AWS Lambda.

Configure the following environment variables in `serverless.yml` so that the bot can posts to your Slack channel:

* `SLACK_API_TOKEN`
* `SLACK_CHANNEL` 

## Contributors

* Raúl Negrón
* Abdiel Aviles