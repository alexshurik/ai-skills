# Browser Login Through a Messaging Account

Add a browser login flow confirmed through the project's existing messaging bot.
The browser starts a short-lived challenge, the user confirms it in a private bot
conversation, and the browser completes login with two independent proofs.

Requirements:

- limit abusive start, polling, and completion requests;
- expire challenges after five minutes;
- consume a successful challenge once;
- issue the project's existing signed browser session;
- keep status polling from exposing the confirmed identity;
- provide production configuration required by the feature.

Use existing project and reference-project integrations where appropriate. Do not
change unrelated authorization behavior.
