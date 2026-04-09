/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FeedbackPayload = {
    recommendation_id: string;
    clinician_id: string;
    action: FeedbackPayload.action;
    free_text?: (string | null);
    patient_id?: string;
};
export namespace FeedbackPayload {
    export enum action {
        ACCEPT = 'accept',
        MODIFY = 'modify',
        REJECT = 'reject',
    }
}

