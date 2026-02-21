# Meta WhatsApp Webhook Echo Lambda

Routes Meta WhatsApp Cloud API webhooks through AWS Lambda (US region) to your
Chatwoot instance, bypassing Hostinger's network routing issues.

## How It Works

```
Meta ──►  Lambda  ──►  Chatwoot (Hostinger, Brazil)
```

- **Verification (GET)**: Lambda checks `hub.verify_token` against your configured
  tokens and responds with the challenge string.
- **Forwarding (POST)**: Lambda reads `entry[].changes[].value.metadata.display_phone_number`
  from the Meta payload and forwards the full JSON body to:
  `{CHATWOOT_BASE_URL}/{+phone_number}`

No explicit phone-number-to-inbox mapping needed — the display phone number in Meta's
payload directly matches the path segment in your Chatwoot webhook URL.

---

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) configured (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed

> No API Gateway needed — the Lambda exposes itself directly via a **Function URL**
> (`*.lambda-url.<region>.on.aws`), which is free and requires no extra infrastructure.

Install SAM CLI on Linux/macOS:
```bash
# macOS
brew install aws/tap/aws-sam-cli

# Linux (via pip)
pip install aws-sam-cli
```

---

## Deploy

### 1. First-time deployment (guided, saves config to `samconfig.toml`)

```bash
sam build
sam deploy --guided
```

When prompted:

| Parameter             | Example value                                                          |
|-----------------------|------------------------------------------------------------------------|
| Stack name            | `meta-wpp-webhook-echo`                                                |
| AWS Region            | `us-east-1`  ← choose a US region to avoid Hostinger routing issues    |
| ChatwootBaseUrl       | `ttps://selfhosted.customdomain.com.br/webhooks/whatsapp`                  |
| VerifyTokens          | `mytoken123,anothertoken456`  ← comma-separated, one per Meta App      |
| ForwardTimeoutSeconds | `10`                                                                   |

At the end, SAM prints:
```
Outputs
-------
WebhookUrl: https://xxxx.execute-api.us-east-1.amazonaws.com/prod/webhook
```

Copy this URL — you'll use it in the Meta Developer Console.

### 2. Subsequent deployments

```bash
sam build && sam deploy
```

---

## Configure Meta

For **each** WhatsApp Business App in the Meta Developer Console:

1. Go to: **App Dashboard → WhatsApp → Configuration → Webhook**
2. Set **Callback URL** to: `https://xxxx.execute-api.us-east-1.amazonaws.com/prod/webhook`
3. Set **Verify Token** to: the token you included in `VerifyTokens` for this App
4. Click **Verify and Save**
5. Subscribe to the **messages** webhook field

> All inboxes under the **same Meta App** share the same webhook URL and verify token.
> Inboxes under **different Meta Apps** each need their own token — add all tokens
> comma-separated in `VerifyTokens`.

---

## Updating Configuration

To change the Chatwoot URL or add/remove verify tokens:

```bash
sam deploy \
  --parameter-overrides \
    ChatwootBaseUrl="ttps://selfhosted.customdomain.com.br/webhooks/whatsapp" \
    VerifyTokens="token1,token2,token3"
```

---

## Monitoring

View Lambda logs in real time:

```bash
sam logs -n meta-wpp-webhook-echo --tail
```

Or in the AWS Console: **CloudWatch → Log Groups → /aws/lambda/meta-wpp-webhook-echo**

---

## Tearing Down

```bash
sam delete
```

---

## Environment Variables Reference

| Variable                 | Description                                                   |
|--------------------------|---------------------------------------------------------------|
| `CHATWOOT_BASE_URL`      | Base URL without trailing slash                               |
| `VERIFY_TOKENS`          | Comma-separated list of accepted Meta verify tokens           |
| `FORWARD_TIMEOUT_SECONDS`| HTTP timeout for Chatwoot calls (default: 10)                 |
