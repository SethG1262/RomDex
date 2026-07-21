# RomDex IGDB proxy deployment

RomDex sends IGDB requests through an authenticated Firebase HTTPS Function.
The Windows application contains no IGDB client secret and never receives the
Twitch access token.

## Before the first deployment

1. Upgrade the Firebase project `romdex-d6b1b` to the Blaze plan.
2. In Firebase Authentication, enable the **Anonymous** sign-in provider.
3. Rotate the Twitch/IGDB client secret before using this function. An older
   secret existed in the repository's `env_copy.txt`; deleting that file does
   not remove it from existing Git history.
4. In Google Cloud **APIs & Services > Credentials**, confirm the bundled
   Firebase API key is restricted to Firebase-related APIs only.
5. Install the Firebase CLI and sign in:

   ```bash
   npm install -g firebase-tools
   firebase login
   firebase use romdex-d6b1b
   ```

## Store the IGDB credentials

Run these commands from the repository root. The CLI securely prompts for each
value, so do not put either value in a command argument or an `.env` file.

```bash
firebase functions:secrets:set IGDB_CLIENT_ID
firebase functions:secrets:set IGDB_CLIENT_SECRET
```

The values are stored in Google Cloud Secret Manager and are exposed only to
the deployed `igdb_proxy` function.

## Deploy

```bash
firebase deploy --only functions:igdb_proxy
```

The desktop app already points to:

```text
https://us-central1-romdex-d6b1b.cloudfunctions.net/igdb_proxy
```

No `.env` file is required on an end user's computer. The Firebase API key and
project ID bundled in RomDex are public client identifiers; Firebase ID-token
verification and Firestore Security Rules enforce access.

## Optional local emulator

For local-only function testing, create `functions/.secret.local` (it is
ignored by Git):

```dotenv
IGDB_CLIENT_ID=your_client_id
IGDB_CLIENT_SECRET=your_rotated_client_secret
```

Start the emulator:

```bash
firebase emulators:start --only functions
```

Then place this optional override in the developer machine's root `.env`:

```dotenv
ROMDEX_IGDB_PROXY_URL=http://127.0.0.1:5001/romdex-d6b1b/us-central1/igdb_proxy
```

Never distribute either development file with a RomDex build.

## Updating a secret later

Set the secret again, then redeploy so the function receives the new version:

```bash
firebase functions:secrets:set IGDB_CLIENT_SECRET
firebase deploy --only functions:igdb_proxy
```
