// Text shown to participants. Keep it here, not in the components, so it can
// be reworded or translated in one place.
const strings = {
  pidNotSet: "PID is not set.",
  projectDeactivated: "This project is deactivated.",
  pidNotFound: "PID not found.",
  projectNotAccessible: "This project is not accessible.",
  // the conversation was not created, so the page has to be reloaded
  reloadAfter: (message: string, seconds: number) =>
    `${message} Reload the page in ${seconds} seconds.`,
  // shown with a message that went back into the input field
  retryAfter: (message: string, seconds: number) => `${message} (${seconds} s)`
};

export default strings;
