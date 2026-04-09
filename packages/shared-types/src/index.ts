/**
 * Shared API contracts — keep in sync with `python/amca_shared_types` Pydantic models.
 */
export type HealthResponse = {
  status: string;
  service: string;
};
