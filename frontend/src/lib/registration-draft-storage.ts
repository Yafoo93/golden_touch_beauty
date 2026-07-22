export type RegistrationDraft = {
  full_name: string;
  email: string;
  phone_number: string;
  terms_privacy_agreed: boolean;
  marketing_consent: boolean;
};

const DRAFT_KEY = "golden-touch-registration-draft";

export function readRegistrationDraft(): Partial<RegistrationDraft> {
  const saved = sessionStorage.getItem(DRAFT_KEY);
  if (!saved) return {};
  const parsed = JSON.parse(saved) as Record<string, unknown>;
  return {
    full_name: typeof parsed.full_name === "string" ? parsed.full_name : "",
    email: typeof parsed.email === "string" ? parsed.email : "",
    phone_number: typeof parsed.phone_number === "string" ? parsed.phone_number : "",
    terms_privacy_agreed: parsed.terms_privacy_agreed === true,
    marketing_consent: parsed.marketing_consent === true,
  };
}

export function writeRegistrationDraft(draft: RegistrationDraft) {
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify({
    full_name: draft.full_name,
    email: draft.email,
    phone_number: draft.phone_number,
    terms_privacy_agreed: draft.terms_privacy_agreed,
    marketing_consent: draft.marketing_consent,
  }));
}

export function clearRegistrationDraft() {
  sessionStorage.removeItem(DRAFT_KEY);
}
