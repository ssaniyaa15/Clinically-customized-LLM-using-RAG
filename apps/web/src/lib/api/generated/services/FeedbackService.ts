/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FeedbackPayload } from '../models/FeedbackPayload';
import type { FeedbackResponse } from '../models/FeedbackResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FeedbackService {
    /**
     * Post Feedback
     * @param requestBody
     * @returns FeedbackResponse Successful Response
     * @throws ApiError
     */
    public static postFeedbackFeedbackPost(
        requestBody: FeedbackPayload,
    ): CancelablePromise<FeedbackResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/feedback',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
