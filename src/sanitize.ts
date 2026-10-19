const HTML_COMMENT_OPEN = /<!--/g;
const CXBOT_MENTION = /@cxbot/gi;
const SUGGESTION_FENCE_LINE = /^\s*```/m;
const ZERO_WIDTH_SPACE = String.fromCharCode(0x200b);

function stripControlChars(text: string): string {
  let out = "";
  for (const ch of text) {
    const code = ch.codePointAt(0) ?? 0;
    const isC0 = code < 32 && code !== 9 && code !== 10;
    if (isC0 || code === 127) continue;
    out += ch;
  }
  return out;
}

export function sanitizeModelText(text: string): string {
  return stripControlChars(text.replace(/\r\n?/g, "\n"))
    .replace(HTML_COMMENT_OPEN, "&lt;!--")
    .replace(CXBOT_MENTION, `@${ZERO_WIDTH_SPACE}cxbot`);
}

export function sanitizePatchText(patch: string): string | undefined {
  const cleaned = stripControlChars(patch.replace(/\r\n?/g, "\n"));
  if (SUGGESTION_FENCE_LINE.test(cleaned)) return undefined;
  if (cleaned.includes("<!--")) return undefined;
  return cleaned;
}
