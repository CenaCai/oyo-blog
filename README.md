# oyo-blog

Auto-sync blog posts from [creditkaagapay.com/blog](https://www.creditkaagapay.com/blog/) to CashOyo platform via Post Push API.

## How it works

1. Fetches latest 10 posts from WordPress REST API
2. Compares against `pushed.json` to find new posts
3. Pushes new posts to CashOyo API (title, content, cover image, link)
4. Records pushed articles in `pushed.json`

## Schedule

Runs daily at UTC 9:00 (PHT 17:00) via GitHub Actions.

## Setup

Add the following secret in repo Settings → Secrets → Actions:

- `CASHOYO_SECRET` — CashOyo Post Push API secret key
