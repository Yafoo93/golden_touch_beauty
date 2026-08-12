export type CustomerConsent = {
  marketing_consent: boolean;
  marketing_consent_updated_at: string;
  photograph_consent: boolean;
  photograph_consent_updated_at: string | null;
  terms_version: string;
  privacy_version: string;
  terms_privacy_accepted_at: string;
};
