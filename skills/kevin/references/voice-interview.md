# Create a personality from a description

Accept a description such as "a confident engineer, dry humor, concise, no arrogance". Turn it into an inspectable voice the user can refine. No particular model, shell or provider is required.

## Interview

Use the description and already approved preferences to resolve known decisions. Ask about gaps and conflicts, not a fixed intake form. Ask one question per turn, include a recommended answer and explain its consequence in one short sentence. Offer two or three meaningful options, plus free text when the host supports it. Use the user's language.

High-value gaps include primary audience/task, what directness should feel like, humor permission, sarcasm boundaries, preferred detail, and phrases or behaviors to avoid. Do not ask for age, diagnosis or private history. Never infer a psychological identity from a character reference. Translate character inspiration into reusable communication traits, without copied dialogue.

Example question for a voice described as "direct but friendly":

> Quando encontrar um bug comprovado, qual abordagem combina mais?
>
> A. Apontar falha e correção diretamente, mantendo respeito. Recomendado: preserva gravidade sem rodeio.
>
> B. Começar com pergunta colaborativa, sem transformar certeza em dúvida.

If an answer contradicts the description, resolve that specific conflict next. "Always sarcastic" and "sensitive disagreements" require a boundary discussion; serious-context humor still remains off. Do not keep interviewing once enough decisions exist to create a useful voice. Offer deeper refinement when the user requests it.

## Compare actual response shapes

Use supplied evidence when authorized. Otherwise label a short scenario as fictional. Show two or three plausible replies with identical facts and commitments, varying only the unresolved expression choice. Ask which is closest and what feels wrong. A choice is style feedback, not permission to send the message.

For example, given fictional evidence "I will look after lunch; tests have not run", compare:

- "I'll take a look after lunch. Tests haven't run yet."
- "Thanks for flagging it. I'll take a look after lunch. Tests haven't run yet."
- "I will review it after lunch. Tests have not run yet."

Do not include a false test claim as a valid option. Do not bundle uncertainty, added promises or more aggression into a style choice. A/B choices cannot justify changing meaning.

Use another short scenario only if it resolves a remaining uncertainty. For a playful voice, include an ordinary invited exchange and a serious incident to show where humor stops. Absence of humor can be the best response even in the ordinary example. Do not reuse one canned joke across all personalities.

## Propose, then save

Present name, description, parent archetype if useful, partial traits, behaviors, avoid list, and the contextual limits. Show a normal-context preview and a serious-context preview. Mark inferred choices and unresolved gaps. Numerical traits are qualitative guidance, not measured user scores.

Explain what will change: one named voice. Leave identity and routing unchanged unless separately requested. Show exact JSON when persisting into Kevin's configuration. Ask for approval of the concrete result before writing a durable preference. Support refinement or cancellation. If tools are unavailable, return the proposed JSON and say it has not been saved. Save no private examples in the voice.

The CLI can help with a deterministic local questionnaire:

```bash
kevin voice create field-engineer --description "Confident, concise, dry humor, no arrogance"
```

TTY mode asks one question at a time with recommendations, offers example choices, prints the proposal and asks whether to save. Noninteractive mode returns the next question; repeat with `--answers answers.json` to supply approved choices. Complete answers emit a proposal. `--save` explicitly persists it.

CLI questions are a fixed local decision tree; they do not semantically analyze the free-form description. The description is retained as model-facing style data, and choices set traits. This agent workflow can perform deeper gap analysis using its model; do not claim the local questionnaire does that automatically.
