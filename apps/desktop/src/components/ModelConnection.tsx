import {
  MODEL_MESSAGES,
  type ModelStatus,
} from "../services/modelAvailability";

export function ModelConnection({
  status,
  busy,
  onCheck,
}: {
  status: ModelStatus | null;
  busy: boolean;
  onCheck: () => void;
}) {
  return (
    <section className="pilot-step" aria-labelledby="model-connection-heading">
      <h2 id="model-connection-heading">Model connection</h2>
      <p>
        This explicit readiness check sends no document text and generates no
        embedding. It may wake the cloud service and incur startup or instance
        charges against the pilot budget. It does not change minimum instances
        or retry a search.
      </p>
      <button className="back" disabled={busy} onClick={onCheck}>
        Check model connection
      </button>
      {status && (
        <div role="status">
          <p>
            Last explicit check:{" "}
            {status.state === "model_deadline"
              ? "The readiness request reached its deadline. No embedding was submitted. Startup or network delay may be involved; the cause is unconfirmed. Wait before explicitly checking again."
              : MODEL_MESSAGES[status.state]}
          </p>
          <p>
            At that check, this local API process had used {status.used} of{" "}
            {status.limit} model attempts. Readiness checks do not consume that
            attempt allowance. This is a local pilot safety limit, not a billing
            or token-usage meter.
          </p>
        </div>
      )}
    </section>
  );
}
