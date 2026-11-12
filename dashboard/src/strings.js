// Text shown to researchers on the usage, limits and embedding screens. Keep it
// here, not in the components, so it can be reworded or translated in one place.

export const usageStrings = {
  tokenUsage: "Token usage",
  perModel: "Per model",
  perConversation: "Per conversation",
  promptTokens: "Prompt tokens",
  completionTokens: "Completion tokens",
  totalTokens: "Total tokens",
  estimatedCostUsd: "Estimated cost (USD)",
  noUsage: "No usage recorded yet.",
  notAvailable: "n/a",
  columns: {
    model: "Model",
    calls: "Calls",
    prompt: "Prompt",
    completion: "Completion",
    total: "Total",
    estCost: "Est. cost",
    conversation: "Conversation",
    participant: "Participant",
    turns: "Turns",
    totalTokens: "Total tokens"
  },
  projectCapUsed: (used, cap, percent) =>
    `${used} of ${cap} project tokens used (${percent}%).`,
  countingNote:
    "Tokens are the counts the model provider reports. Where a provider reports none (participant chats on Azure API versions before 2024-09-01), they are tiktoken (cl100k_base) estimates. Costs use the list prices configured in the backend",
  errorGettingUsage: "There was an error to get the token usage."
};

export const limitsStrings = {
  pageTitle: projectId => `Usage & limits "${projectId}"`,
  breadcrumbProject: "Project",
  breadcrumbUsage: "Usage & limits",
  heading: "Limits",
  intro:
    "Leave a field empty for no limit. The allowlist takes one participant ID per line; when it is empty every participant may join. The rate limit counts conversation starts and messages within the window, per participant ID (or per IP address when the chat URL has no participant ID) or per IP address.",
  noLimit: "No limit",
  mustBePositive: "Must be a positive integer",
  windowLabel: "Rate limit window (seconds)",
  windowInvalid: "Must be between 1 and 86400 seconds",
  keyLabel: "Rate limit counted per",
  keyParticipant: "Participant ID",
  keyIp: "IP address",
  allowlistLabel: "Participant allowlist",
  allowlistPlaceholder: "Everyone allowed",
  originsLabel: "Allowed embedding origins",
  originsPlaceholder: "Any site may embed the chat",
  originsHelper:
    "One origin per line, e.g. https://*.qualtrics.com. Only these sites may show the chat in an iframe.",
  save: "Save limits",
  saved: "Limits updated successfully.",
  saveFailed: "Failed to update limits!",
  errorSaving: message => `There was an error updating the limits: ${message}`,
  errorGetting: "There was an error to get the limits.",
  fieldLabels: {
    max_conversations_per_participant: "Max conversations per participant",
    max_turns: "Max turns per conversation",
    max_tokens_per_conversation: "Token cap per conversation",
    max_tokens_per_project: "Token cap per project",
    rate_limit_messages: "Rate limit (starts and messages per window)"
  }
};

// shown by the info button next to each limit
export const limitHelp = {
  max_conversations_per_participant: {
    title: "Max conversations per participant",
    what: "How many conversations one participant_id may send messages in, in this project. Opening the chat without sending a message (e.g. a page reload) does not count. In a multi-round study, the first conversation of rounds 2, 3, ... continues round 1 and is not counted once the participant wrote in the previous round; a second conversation of the same round is counted. Not applied when the chat URL has no participant_id.",
    example:
      "1: a participant who has chatted and then reloads the survey page cannot start a second chat.",
    combined:
      "With a participant allowlist, only the listed IDs can chat, each at most once. The allowlist also makes the participant_id required, so this limit always applies."
  },
  max_turns: {
    title: "Max turns per conversation",
    what: "How many messages a participant may send in one conversation. In multi-round studies, messages copied from earlier rounds do not count. The chat closes after the last allowed message has been answered.",
    example: "10: after the 10th answered message the chat input closes.",
    combined:
      "With max conversations per participant 1, each participant gets at most 10 messages in total. With a token cap per conversation, whichever is reached first ends the chat."
  },
  max_tokens_per_conversation: {
    title: "Token cap per conversation",
    what: "Prompt and completion tokens one conversation may use. Each reply sends the whole chat history again, so usage grows with every turn.",
    example:
      "50000: a long chat ends once about 50,000 tokens are used, even if turns are left.",
    combined:
      "With max turns 20, it stops participants who paste long texts from making 20 turns expensive. Turns limit normal chats, the token cap limits unusual ones."
  },
  max_tokens_per_project: {
    title: "Token cap per project",
    what: "Total tokens all conversations of this project may use. Once reached, no new chats start and running chats end.",
    example:
      "5000000: the project stops at 5 million tokens. The usage table above shows how close you are and the estimated cost.",
    combined:
      "With a token cap per conversation of 50000, 5000000 covers at least 100 conversations that use their full cap. Set it to about participants × conversation cap, plus a margin."
  },
  rate_limit_messages: {
    title: "Rate limit",
    what: "How many conversation starts and messages are allowed within the rate limit window. Further attempts get a 'please wait' notice and the message returns to the input field.",
    example:
      "10 with a window of 60 seconds: at most 10 starts and messages per minute. A participant typing normally never hits this, a script sending messages does.",
    combined:
      "Counted per participant ID, each participant has their own limit. Counted per IP address, everyone behind the same IP shares it, so allow more for lab sessions on one network."
  },
  rate_limit_window_seconds: {
    title: "Rate limit window",
    what: "The time span the rate limit counts over, from 1 to 86400 seconds (one day). Only used when the rate limit is set. The window slides: a slot frees up as soon as the oldest counted message is older than the window.",
    example:
      "30 with a rate limit of 5: at most 5 starts and messages in any 30 seconds.",
    combined:
      "A rate limit of 100 with a window of 86400 is a daily quota of 100 starts and messages per participant, across all their conversations. It adds to max turns, which limits one conversation."
  },
  rate_limit_key: {
    title: "Rate limit counted per",
    what: "Participant ID counts per participant_id from the chat URL and falls back to the IP address when the URL has none. IP address always counts per IP.",
    example:
      "Participant ID for a Prolific study where every URL carries the participant's ID; IP address when the URL has no ID or anyone could invent one.",
    combined:
      "With a participant allowlist, Participant ID is the right choice because IDs cannot be invented. Behind a proxy or ingress, set TRUST_X_FORWARDED_FOR in the backend, or all participants share the proxy's IP."
  },
  participant_allowlist: {
    title: "Participant allowlist",
    what: "Participant IDs (e.g. Prolific IDs) allowed to start a conversation, one per line or comma-separated. Empty means everyone may join.",
    example:
      "Paste the Prolific IDs of your approved participants; a chat URL with any other ID, or without one, shows 'You are not registered for this study'.",
    combined:
      "With max conversations per participant 1, each listed participant chats exactly once. With allowed embedding origins, someone who copies the iframe to another site is blocked, and opening the link directly still needs a listed ID."
  },
  allowed_embed_origins: {
    title: "Allowed embedding origins",
    what: "Sites allowed to show the chat in an iframe, one origin per line. *. allows all subdomains. Empty means any site may embed it. Opening the chat link directly, e.g. the test chat, keeps working.",
    example:
      "https://*.qualtrics.com: the chat works inside your Qualtrics survey, but not when someone embeds it on their own site.",
    combined:
      "It stops other sites from using your chat and token budget, but not direct visits to the link. Add a participant allowlist and a rate limit for those."
  }
};

export const infoStrings = {
  about: title => `About ${title}`,
  example: "Example",
  combined: "Combined with other limits"
};

export const projectStrings = {
  defaultModel: model => `Default model : ${model || "server default"}`,
  embedIntro:
    "Embed the chat in your survey (replace PARTICIPANT_ID with your platform's participant variable)",
  copyIframe: "Copy iframe code",
  openTestChat: "Open test chat",
  usageIntro: "Token usage, estimated cost and participant limits",
  usageButton: "Usage & limits",
  modelHeading: "Model",
  modelLabel: "used when the chat URL has no model parameter"
};
