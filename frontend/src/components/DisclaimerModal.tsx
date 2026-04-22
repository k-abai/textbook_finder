import { useMemo, useState } from "react";

import { writePolicyAcceptance } from "../lib/libraryMetadata";

export const POLICY_VERSION = "2026-04-22";
export const REQUIRED_ATTESTATION =
  "I have rights or permission to access/download this material.";

type DisclaimerModalProps = {
  isOpen: boolean;
  onAccepted: (payload: { policyVersion: string; acceptedAt: string }) => void;
};

export default function DisclaimerModal({ isOpen, onAccepted }: DisclaimerModalProps) {
  const [typedAttestation, setTypedAttestation] = useState("");
  const [hasConfirmed, setHasConfirmed] = useState(false);

  const canAccept = useMemo(() => {
    return hasConfirmed && typedAttestation.trim() === REQUIRED_ATTESTATION;
  }, [hasConfirmed, typedAttestation]);

  if (!isOpen) {
    return null;
  }

  const handleAccept = () => {
    if (!canAccept) {
      return;
    }

    const acceptedAt = new Date().toISOString();
    writePolicyAcceptance({
      version: POLICY_VERSION,
      acceptedAt,
      attestation: REQUIRED_ATTESTATION,
    });

    onAccepted({ policyVersion: POLICY_VERSION, acceptedAt });
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="policy-title">
      <div className="modal">
        <h2 id="policy-title">Policy acknowledgement required</h2>
        <p>
          Policy version: <strong>{POLICY_VERSION}</strong>
        </p>
        <p>
          By searching, you agree to use this tool only for lawful and authorized access,
          including compliance with copyright law and your campus policies.
        </p>
        <p>
          To continue, type the exact statement below:
          <br />
          <code>{REQUIRED_ATTESTATION}</code>
        </p>

        <textarea
          aria-label="Attestation text"
          value={typedAttestation}
          onChange={(event) => setTypedAttestation(event.target.value)}
          rows={3}
        />

        <label>
          <input
            type="checkbox"
            checked={hasConfirmed}
            onChange={(event) => setHasConfirmed(event.target.checked)}
          />
          I confirm I read and agree to this versioned policy.
        </label>

        <button type="button" disabled={!canAccept} onClick={handleAccept}>
          Enable search
        </button>
      </div>
    </div>
  );
}
