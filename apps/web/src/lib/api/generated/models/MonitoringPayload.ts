/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type MonitoringPayload = {
    reference: Array<Record<string, number>>;
    current: Array<Record<string, number>>;
    predictions: Array<number>;
    ground_truth: Array<number>;
    sensitive_attrs: Array<number>;
    error_rate: number;
};

