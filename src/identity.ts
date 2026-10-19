export type IdentityVerdict = "self" | "scanner" | "human-command" | "ignore";

export interface IdentityRegistry {
  scanner_logins?: string[];
  scanner_login_patterns?: string[];
  body_fingerprints?: string[];
  human_author_associations?: string[];
}

export interface Actor {
  login: string;
  type?: string;
  authorAssociation?: string;
  body?: string;
}

export const DEFAULT_SELF_LOGINS = ["github-actions[bot]", "cxbot[bot]", "cx-prbot[bot]"];

const DEFAULT_SCANNER_LOGIN_PATTERNS = [
  "coderabbitai",
  "trufflehog",
  "checkmarx",
  "^cx-",
  "sonar",
  "semgrep"
];

const DEFAULT_BODY_FINGERPRINTS = [
  "<!-- cr-comment:",
  "<!-- CodeRabbit review command invocation:",
  "<!-- This is an auto-generated comment by CodeRabbit -->",
  "::error::",
  "trufflehog:"
];

const CXBOT_MARKER = "<!-- cxbot:";

export function compilePatterns(patterns: string[]): RegExp[] {
  return patterns.map((p) => new RegExp(p, "i"));
}

function matchesAny(value: string, patterns: RegExp[]): boolean {
  return patterns.some((re) => re.test(value));
}

function isSelfLogin(login: string, selfLogins: string[]): boolean {
  return selfLogins.some((self) => self.toLowerCase() === login.toLowerCase());
}

export function classifyActor(
  actor: Actor,
  registry: IdentityRegistry = {},
  selfLogins: string[] = DEFAULT_SELF_LOGINS
): IdentityVerdict {
  const login = actor.login;
  const body = actor.body ?? "";

  const fingerprints = compilePatterns([
    ...(registry.body_fingerprints ?? []),
    ...DEFAULT_BODY_FINGERPRINTS
  ]);
  const scannerLoginPatterns = compilePatterns([
    ...(registry.scanner_login_patterns ?? []),
    ...DEFAULT_SCANNER_LOGIN_PATTERNS
  ]);
  const explicitScannerLogins = (registry.scanner_logins ?? []).map(
    (l) => new RegExp(`^${l.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`, "i")
  );

  if (body.includes(CXBOT_MARKER)) return "self";

  if (isSelfLogin(login, selfLogins)) {
    return matchesAny(body, fingerprints) ? "scanner" : "self";
  }

  if (matchesAny(login, scannerLoginPatterns) || matchesAny(login, explicitScannerLogins)) {
    return "scanner";
  }

  if (actor.type === "Bot") {
    return "ignore";
  }

  if (matchesAny(body, fingerprints)) return "ignore";

  const allowedAssociations = registry.human_author_associations ?? [
    "OWNER",
    "MEMBER",
    "COLLABORATOR"
  ];
  if (!allowedAssociations.includes(actor.authorAssociation ?? "NONE")) {
    return "ignore";
  }

  return "human-command";
}
