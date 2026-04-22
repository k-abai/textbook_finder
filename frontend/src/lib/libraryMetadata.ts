export const LIBRARY_METADATA_KEY = "textbook_finder.library_metadata";

export type PolicyAcceptance = {
  version: string;
  acceptedAt: string;
  attestation: string;
};

export type LibraryMetadata = {
  policyAcceptance?: PolicyAcceptance;
  updatedAt: string;
};

export function readLibraryMetadata(): LibraryMetadata {
  try {
    const raw = localStorage.getItem(LIBRARY_METADATA_KEY);
    if (!raw) {
      return { updatedAt: new Date().toISOString() };
    }
    const parsed = JSON.parse(raw) as LibraryMetadata;
    return {
      ...parsed,
      updatedAt: parsed.updatedAt ?? new Date().toISOString(),
    };
  } catch {
    return { updatedAt: new Date().toISOString() };
  }
}

export function writePolicyAcceptance(acceptance: PolicyAcceptance): LibraryMetadata {
  const next: LibraryMetadata = {
    ...readLibraryMetadata(),
    policyAcceptance: acceptance,
    updatedAt: new Date().toISOString(),
  };
  localStorage.setItem(LIBRARY_METADATA_KEY, JSON.stringify(next));
  return next;
}
