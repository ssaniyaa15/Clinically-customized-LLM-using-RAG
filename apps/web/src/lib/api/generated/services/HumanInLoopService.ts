/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConfirmPayload } from '../models/ConfirmPayload';
import type { GateActionResponse } from '../models/GateActionResponse';
import type { OverridePayload } from '../models/OverridePayload';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HumanInLoopService {
    /**
     * Confirm Recommendation
     * @param requestBody
     * @returns GateActionResponse Successful Response
     * @throws ApiError
     */
    public static confirmRecommendationGateConfirmPost(
        requestBody: ConfirmPayload,
    ): CancelablePromise<GateActionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/gate/confirm',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Override Recommendation
     * @param requestBody
     * @returns GateActionResponse Successful Response
     * @throws ApiError
     */
    public static overrideRecommendationGateOverridePost(
        requestBody: OverridePayload,
    ): CancelablePromise<GateActionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/gate/override',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
